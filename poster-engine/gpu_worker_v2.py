"""Feature 3 opt-in GPU worker implementations; NEVER import inside HTTP Functions.

In production, invoke only after OptionalGPUProvider gates license/cost/tenant,
server-authorized asset bytes and quota/lease fencing. Model snapshot must be
pre-cached by an approved deployment and network-disabled at inference time.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from ai_providers_v2 import ProviderBlocked


def _image_bytes(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= 25 * 1024 * 1024:
        raise ProviderBlocked("Invalid authorized source image")
    try:
        with Image.open(BytesIO(raw)) as image:
            if (image.width > 8192 or image.height > 8192
                or image.width * image.height > 24_000_000
                or getattr(image, "n_frames", 1) != 1):
                raise ProviderBlocked("Unsafe image size or animation")
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ProviderBlocked("Could not decode authorized source") from exc


class OfflineFluxKlein4B:
    """True Diffusers worker when preinstalled CUDA + reviewed local 4B weights.

    No package installation/model downloads happen on module import. Output
    contains imagery only: exact business words/offers MUST be placed by Pillow.
    """
    def __init__(self, weights_directory, *, height=768, width=768, steps=4):
        self.weights = Path(weights_directory)
        self.height, self.width, self.steps = height, width, steps
        if (not self.weights.is_dir() or self.weights.is_symlink()
            or height not in (512, 768, 1024) or width not in (512, 768, 1024)
            or steps != 4):
            raise ProviderBlocked("Only approved preinstalled FLUX.2 Klein 4B weights allowed")
        self.pipeline = None
        # Runtime proof is never inferred merely from a configured CUDA Docker image.
        self.actual_cuda_verified = False

    def __call__(self, job, inputs):
        self.actual_cuda_verified = False
        if job.capability not in ("text_to_image", "image_edit", "human_model", "background"):
            raise ProviderBlocked("Unsupported FLUX worker mode")
        if job.capability == "image_edit" and len(inputs) != 1:
            raise ProviderBlocked("Image edit needs one authorized reference")
        if job.capability != "image_edit" and inputs:
            raise ProviderBlocked("Unexpected image references")
        if not job.prompt.strip():
            raise ProviderBlocked("Approved visual brief required")
        try:
            import torch
            from diffusers import Flux2KleinPipeline
        except ImportError as exc:
            raise ProviderBlocked("Approved GPU inference dependencies not installed") from exc
        if not torch.cuda.is_available():
            raise ProviderBlocked("CUDA GPU not available")
        if self.pipeline is None:
            # Feature5 A100 was never provisioned. Feature3 prefers cheaper T4.
            # Tesla T4 (SM 7.5) has FP16 but NO native BF16: never hardcode BF16.
            capability = torch.cuda.get_device_capability()
            if not isinstance(capability, tuple) or capability[0] < 7:
                raise ProviderBlocked("Unsupported CUDA compute capability")
            has_bf16 = (capability[0] >= 8 and
                        bool(getattr(torch.cuda, "is_bf16_supported", lambda: False)()))
            gpu_dtype = torch.bfloat16 if has_bf16 else torch.float16
            available_vram = torch.cuda.get_device_properties(0).total_memory
            if available_vram < 14 * 1024 ** 3:
                raise ProviderBlocked("Insufficient CUDA memory for reviewed FLUX.2 Klein 4B")
            pipe = Flux2KleinPipeline.from_pretrained(
                str(self.weights), torch_dtype=gpu_dtype,
                local_files_only=True,
            )
            if available_vram < 20 * 1024 ** 3:
                # T4's 16GB budget needs verified Accelerate CPU offload.
                # Do NOT attempt a risky full GPU .to() as fallback.
                try:
                    pipe.enable_model_cpu_offload()
                except (AttributeError, ImportError, RuntimeError) as exc:
                    raise ProviderBlocked("T4 requires compatible CPU offload setup") from exc
            else:
                pipe.to("cuda")
            self.pipeline = pipe
        brief = job.prompt.strip()
        if job.capability == "human_model":
            brief = "Photorealistic adult fashion model, professional clothing advertisement. " + brief
        kwargs = {"prompt": brief, "height": self.height, "width": self.width,
                  "num_inference_steps": self.steps, "guidance_scale": 1.0,
                  "generator": torch.Generator(device="cuda").manual_seed(
                      int(UUID(job.job_id)) % (2 ** 31)),
                  }
        if inputs:
            kwargs["image"] = _image_bytes(next(iter(inputs.values())))
        output = self.pipeline(**kwargs).images[0]
        # Synchronize kernels before recording a real-GPU receipt. Merely importing
        # torch or returning valid Pillow bytes does not prove CUDA inference.
        torch.cuda.synchronize(0)
        if int(torch.cuda.max_memory_allocated(0)) <= 0:
            raise ProviderBlocked("CUDA pipeline did not allocate device memory")
        self.actual_cuda_verified = True
        if not isinstance(output, Image.Image):
            raise ProviderBlocked("FLUX failed to return an image")
        buffer = BytesIO()
        output.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()


class ReviewedTryOn:
    """FASHN-compatible custom worker with a *commercially reviewed parser*.

    The upstream TryOnPipeline automatically loads NVIDIA-derived parser
    weights. It is intentionally NOT instantiated here; a reviewed replacement
    must be injected by the deployment team with matching label semantics.
    """
    def __init__(self, reviewed_pipeline_factory=None, *, parser_approval=None):
        if (not callable(reviewed_pipeline_factory)
            or not isinstance(parser_approval, dict)
            or parser_approval.get("commercial_use_approved") is not True
            or not parser_approval.get("component_sha")
            or not parser_approval.get("weight_license_evidence")):
            raise ProviderBlocked("Compliant parser replacement/weights not approved")
        self.pipeline_factory = reviewed_pipeline_factory

    def __call__(self, job, inputs):
        if job.capability != "virtual_try_on" or len(job.source_asset_ids) != 2:
            raise ProviderBlocked("Invalid try-on operation")
        garment, person = (_image_bytes(inputs[key]) for key in job.source_asset_ids)
        pipeline = self.pipeline_factory()
        if not callable(pipeline):
            raise ProviderBlocked("Invalid patched VTON pipeline")
        result = pipeline(person_image=person, garment_image=garment,
                          category=job.category)
        if not getattr(result, "images", None) or not isinstance(result.images[0], Image.Image):
            raise ProviderBlocked("Try-on did not generate an image")
        buffer = BytesIO()
        result.images[0].convert("RGB").save(buffer, "PNG")
        return buffer.getvalue()


class ReviewedBackgroundRemoval:
    """Explicit licensed segmentation runner; never rembg's auto-download default."""
    def __init__(self, remove_fn=None, *, model_provenance=None):
        if (not callable(remove_fn) or not isinstance(model_provenance, dict)
            or model_provenance.get("commercial_use_approved") is not True
            or not model_provenance.get("weight_sha256")
            or not model_provenance.get("model_name")):
            raise ProviderBlocked("Background-removal model licensing incomplete")
        self.remove_fn = remove_fn

    def __call__(self, job, inputs):
        if job.capability != "background_remove" or len(inputs) != 1:
            raise ProviderBlocked("Background removal needs exactly one private source")
        original = _image_bytes(next(iter(inputs.values())))
        output = self.remove_fn(original)
        if not isinstance(output, Image.Image):
            raise ProviderBlocked("Invalid segmentation result")
        buffer = BytesIO()
        output.save(buffer, "PNG")
        return buffer.getvalue()
