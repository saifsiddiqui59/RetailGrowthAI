"""GPU-OFF ComfyUI API graph constructors for staged FLUX.2 and Wan2.2 weights.

Source references:
Comfy-Org/workflow_templates@e7cd011d4ded3411c2f481200544f0be6fdc962e:
  templates/image_flux2_klein_text_to_image.json (distilled subgraph)
  templates/image_flux2_klein_image_edit_4b_distilled.json
  templates/video_wan2_2_5B_ti2v.json
Comfy-Org/ComfyUI@79cf64c21a1dba50749945ba9fe2e3a692f45438
These API graphs use the native nodes and staged checkpoint filenames.
Never submit them to a live ComfyUI server from source tests.
"""
from __future__ import annotations
import re

CHECKPOINTS = {
    "flux": ("flux-2-klein-4b.safetensors", "qwen_3_4b.safetensors", "flux2-vae.safetensors"),
    "wan": ("wan2.2_ti2v_5B_fp16.safetensors", "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "wan2.2_vae.safetensors"),
}
SAFE_INPUT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,128}\.(?:png|jpg|jpeg|webp)$")
SAFE_OUTPUT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_/-]{0,110}$")


class WorkflowError(ValueError):
    pass


def _text(s):
    if not isinstance(s, str) or not s.strip() or len(s) > 3000 or any(ord(ch) < 32 and ch not in "\n\t" for ch in s):
        raise WorkflowError("Invalid narrative prompt")
    return s.strip()


def _dim(x, *, minimum=256, maximum=1280, multiple=32):
    if type(x) is not int or not minimum <= x <= maximum or x % multiple:
        raise WorkflowError("Dimension outside reviewed profile")
    return x


def _seed(value):
    if type(value) is not int or not 0 <= value < 2**53:
        raise WorkflowError("Random seed must be explicit and bounded")
    return value


def _filename(value):
    if not isinstance(value, str) or not SAFE_INPUT.fullmatch(value) or ".." in value or "/" in value or "\\" in value:
        raise WorkflowError("ComfyUI input must be a validated private staging basename")
    return value


def _prefix(value):
    if not isinstance(value,str) or not SAFE_OUTPUT.fullmatch(value) or value.startswith("/") or ".." in value:
        raise WorkflowError("Output filename prefix must be private and bounded")
    return value


def _node(nodes, key, kind, **inputs):
    nodes[str(key)] = {"class_type": kind, "inputs": inputs}


def flux_klein_4b(*, prompt, seed, width=1024, height=1024, approved_input_file=None, output_prefix="rgai/feature3"):
    """FLUX.2 Klein distilled 4B T2I; optional I2I references one staged owned image.

    Caller MUST verify authenticated shop, copyright/consent and private input
    bytes before placing an image in the private worker's input folder.
    """
    prompt = _text(prompt)
    seed = _seed(seed)
    width = _dim(width, maximum=1536, multiple=16)
    height = _dim(height, maximum=1536, multiple=16)
    prefix = _prefix(output_prefix)
    input_name = _filename(approved_input_file) if approved_input_file is not None else None
    model, clip, vae = CHECKPOINTS["flux"]
    n = {}
    _node(n, 1, "UNETLoader", unet_name=model, weight_dtype="default")
    _node(n, 2, "CLIPLoader", clip_name=clip, type="flux2", device="default")
    _node(n, 3, "VAELoader", vae_name=vae)
    _node(n, 4, "CLIPTextEncode", clip=["2",0], text=prompt)
    _node(n, 5, "ConditioningZeroOut", conditioning=["4",0])
    positive = ["4",0]
    if input_name is not None:
        _node(n, 16, "LoadImage", image=input_name)
        _node(n, 17, "VAEEncode", pixels=["16",0], vae=["3",0])
        _node(n, 18, "ReferenceLatent", conditioning=positive, latent=["17",0])
        positive = ["18",0]
    _node(n, 6, "CFGGuider", model=["1",0], positive=positive, negative=["5",0], cfg=1)
    _node(n, 7, "EmptyFlux2LatentImage", width=width, height=height, batch_size=1)
    _node(n, 8, "RandomNoise", noise_seed=seed)
    _node(n, 9, "KSamplerSelect", sampler_name="euler")
    _node(n, 10, "Flux2Scheduler", steps=4, width=width, height=height)
    _node(n, 11, "SamplerCustomAdvanced", noise=["8",0], guider=["6",0], sampler=["9",0], sigmas=["10",0], latent_image=["7",0])
    _node(n, 12, "VAEDecode", samples=["11",0], vae=["3",0])
    _node(n, 13, "SaveImage", images=["12",0], filename_prefix=prefix)
    return {"prompt": n}


def wan22_ti2v_5b(*, prompt, seed, approved_input_file=None, width=1280, height=704, frames=121, fps=24, output_prefix="rgai/feature5"):
    """Official native Wan2.2 5B hybrid TI2V nodes; optional start_image enables I2V."""
    prompt = _text(prompt)
    seed = _seed(seed)
    width = _dim(width, maximum=1280, multiple=32)
    height = _dim(height, maximum=1280, multiple=32)
    if (width,height) not in ((704,1280),(1280,704)):
        raise WorkflowError("Pinned Wan TI2V-5B supports only native 704x1280 or 1280x704")
    if type(frames) is not int or frames != 121:
        raise WorkflowError("Approved Wan native profile requires 121 frames (~5s at 24fps)")
    if fps != 24 or type(fps) is not int:
        raise WorkflowError("Only 24fps is pre-reviewed")
    prefix = _prefix(output_prefix)
    input_name = _filename(approved_input_file) if approved_input_file is not None else None
    model, clip, vae = CHECKPOINTS["wan"]
    n = {}
    _node(n, 1, "UNETLoader", unet_name=model, weight_dtype="default")
    _node(n, 2, "CLIPLoader", clip_name=clip, type="wan", device="default")
    _node(n, 3, "VAELoader", vae_name=vae)
    _node(n, 4, "CLIPTextEncode", clip=["2",0], text=prompt)
    _node(n, 5, "CLIPTextEncode", clip=["2",0], text="low quality, deformed anatomy, extra fingers, flicker, unreadable embedded text")
    latent_inputs={"vae":["3",0], "width":width, "height":height, "length":frames, "batch_size":1}
    if input_name is not None:
        _node(n, 6, "LoadImage", image=input_name)
        latent_inputs["start_image"]=["6",0]
    _node(n, 7, "Wan22ImageToVideoLatent", **latent_inputs)
    _node(n, 8, "ModelSamplingSD3", model=["1",0], shift=8)
    _node(n, 9, "KSampler", model=["8",0], positive=["4",0], negative=["5",0],
          latent_image=["7",0], seed=seed, steps=20, cfg=5, sampler_name="uni_pc", scheduler="simple", denoise=1)
    _node(n, 10, "VAEDecode", samples=["9",0], vae=["3",0])
    _node(n, 11, "CreateVideo", images=["10",0], fps=fps)
    _node(n, 12, "SaveVideo", video=["11",0], filename_prefix=prefix, format={"format":"mp4","codec":{"codec":"h264"}})
    return {"prompt":n}


def offline_graph_validate(payload):
    """CPU-only checks, not proof that ComfyUI runtime accepts/executed nodes."""
    if not isinstance(payload,dict) or not isinstance(payload.get("prompt"),dict):
        raise WorkflowError("Expected a ComfyUI API prompt")
    nodes=payload["prompt"]
    for key,node in nodes.items():
        if not isinstance(node,dict) or not isinstance(node.get("class_type"),str) or not isinstance(node.get("inputs"),dict):
            raise WorkflowError("Malformed API node")
        for value in node["inputs"].values():
            if isinstance(value,list):
                if len(value)!=2 or not isinstance(value[0],str) or value[0] not in nodes or type(value[1]) is not int or value[1]<0:
                    raise WorkflowError("Broken API node link")
    return len(nodes)
