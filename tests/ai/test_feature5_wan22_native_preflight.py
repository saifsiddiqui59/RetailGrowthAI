"""CPU-only pinned native ComfyUI release preflight: fake locks are not paid approval."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from feature5_motion.infra.feature35_comfy_api_graphs import wan22_ti2v_5b
from feature5_motion.infra.wan22_native_preflight import (
    validate_native_graph_against_object_info,
    validate_runtime_lock, check_small_safetensors_header,
    REQUIRED_PACKAGES,
)
from feature5_motion.wan22_motion_adapter import (
    WanCompatibilityError, COMFY_SOURCE, WAN_SOURCE,
)

IMAGE = "registry.example.invalid/retailgrowth/wan@sha256:" + "a"*64
BASE = "nvcr.io/nvidia/pytorch@sha256:" + "b"*64


def fabricated_object_info(graph):
    """Synthetic test shape, NOT read from ComfyUI /object_info."""
    nodes = {}
    for entry in graph["prompt"].values():
        name = entry["class_type"]
        names = set(entry["inputs"])
        # These are official optional Wan22ImageToVideoLatent inputs;
        # exercise native I2V and T2V using one declared schema.
        required = {k: ["STRING",{}] for k in names}
        optional = {}
        if name == "Wan22ImageToVideoLatent":
            required.pop("start_image",None)
            optional["start_image"]=["IMAGE",{}]
        if name == "SaveVideo":
            # Actual pinned node advertises a hidden optional codec field.
            optional["codec"]=["COMBO",{}]
        for model in ("unet_name","clip_name","vae_name"):
            if model in required:
                required[model] = [[entry["inputs"][model]],{}]
        nodes[name] = {"input":{"required":required,"optional":optional}}
    return nodes


def fake_lock():
    wheels={p:{"version":"1.2.3","sha256":"c"*64} for p in REQUIRED_PACKAGES}
    return {
        "schema":"retailgrowth.wan22.runtime-lock.v1",
        "source_commit":COMFY_SOURCE,
        "wan_source_commit":WAN_SOURCE,
        "image":IMAGE,"base_image":BASE,"python_version":"3.12.9",
        "wheels_sha256":wheels,
        "source_license_reviewed":True,
        "comfy_gpl_distribution_reviewed":True,
        "checkpoint_licenses_reviewed":True,
        "cuda_and_nvidia_eula_reviewed":True,
        "runtime_gpu_enabled":False,
    }


class WanPinnedNativePreflightTests(unittest.TestCase):
    def test_real_graph_shape_offline_with_synthetic_object_info(self):
        for first_frame in (None,"approved_private.png"):
            with self.subTest(first_frame=first_frame):
                graph=wan22_ti2v_5b(prompt="Stable kurti walk in one shot",
                                    seed=3,approved_input_file=first_frame,
                                    width=704,height=1280)
                obj=fabricated_object_info(graph)
                self.assertTrue(validate_native_graph_against_object_info(graph,obj))
                inputs=graph["prompt"]["12"]["inputs"]
                self.assertEqual(inputs["format"],{"format":"mp4","codec":{"codec":"h264"}})
                self.assertNotIn("codec",inputs)

    def test_runtime_drift_wrong_codec_and_mutated_optional_inputs_denied(self):
        graph=wan22_ti2v_5b(prompt="Approved real camera move",seed=9,
                            approved_input_file="first_frame.png",width=704,height=1280)
        info=fabricated_object_info(graph)
        wrong=copy.deepcopy(graph)
        wrong["prompt"]["12"]["inputs"]["codec"]="auto"
        with self.assertRaisesRegex(WanCompatibilityError,"dynamic MP4/H264"):
            validate_native_graph_against_object_info(wrong,info)
        wrong=copy.deepcopy(graph)
        wrong["prompt"]["12"]["inputs"]["format"]="auto"
        with self.assertRaises(WanCompatibilityError):
            validate_native_graph_against_object_info(wrong,info)
        wrong=copy.deepcopy(graph)
        wrong["prompt"]["6"]["inputs"]["image"]="new_unreviewed.png"
        info2=copy.deepcopy(info)
        del info2["LoadImage"]["input"]["required"]["image"]
        with self.assertRaisesRegex(WanCompatibilityError,"Unsupported Comfy input"):
            validate_native_graph_against_object_info(wrong,info2)
        wrong=copy.deepcopy(graph)
        wrong["prompt"]["1"]["inputs"]["unet_name"]="wrong.safetensors"
        with self.assertRaisesRegex(WanCompatibilityError,"checkpoint changed"):
            validate_native_graph_against_object_info(wrong,info)
        info3=copy.deepcopy(info)
        info3["UNETLoader"]["input"]["required"]["unet_name"] = [["other.safetensors"],{}]
        with self.assertRaisesRegex(WanCompatibilityError,"not installed"):
            validate_native_graph_against_object_info(graph,info3)
        info4=copy.deepcopy(info)
        del info4["Wan22ImageToVideoLatent"]["input"]["required"]["width"]
        with self.assertRaises(WanCompatibilityError):
            validate_native_graph_against_object_info(graph,info4)

    def test_pinned_wheel_lock_requires_independently_reviewed_digests(self):
        lock=fake_lock()
        self.assertTrue(validate_runtime_lock(lock,approved_image_digest=IMAGE,
                    reviewed_wheel_sha256=copy.deepcopy(lock["wheels_sha256"])))
        examples=[
            ("base_image","nvidia/cuda:latest"),
            ("image","registry.example.invalid/retailgrowth/wan:latest"),
            ("source_commit","0"*40),
            ("comfy_gpl_distribution_reviewed",False),
            ("runtime_gpu_enabled",True),
        ]
        for key,value in examples:
            bad=copy.deepcopy(lock)
            bad[key]=value
            with self.subTest(key=key),self.assertRaises(WanCompatibilityError):
                validate_runtime_lock(bad,approved_image_digest=IMAGE,
                    reviewed_wheel_sha256=lock["wheels_sha256"])
        with self.assertRaises(WanCompatibilityError):
            validate_runtime_lock(lock,approved_image_digest=BASE,
                                  reviewed_wheel_sha256=lock["wheels_sha256"])
        broken=copy.deepcopy(lock)
        broken["wheels_sha256"].pop("torch")
        with self.assertRaises(WanCompatibilityError):
            validate_runtime_lock(broken,approved_image_digest=IMAGE,
                                  reviewed_wheel_sha256=broken["wheels_sha256"])
        broken=copy.deepcopy(lock)
        broken["wheels_sha256"]["torch"]["sha256"]="d"*64
        with self.assertRaises(WanCompatibilityError):
            validate_runtime_lock(broken,approved_image_digest=IMAGE,
                                  reviewed_wheel_sha256=lock["wheels_sha256"])

    def test_small_safetensors_header_is_not_weight_sha_verification(self):
        header=json.dumps({"weight":{"dtype":"F16","shape":[2],"data_offsets":[0,4]}}).encode()
        content=len(header).to_bytes(8,"little")+header+b"abcd"
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            a=root/"fixture.safetensors";a.write_bytes(content)
            proof=check_small_safetensors_header(a,expected_size=len(content))
            self.assertFalse(proof["model_sha256_verified"])
            self.assertFalse(proof["gpu_started"])
            self.assertEqual(proof["stat_bytes"],len(content))
            with self.assertRaises(WanCompatibilityError):
                check_small_safetensors_header(a,expected_size=len(content)+1)
            broken=root/"bad.safetensors"
            broken.write_bytes((9999999).to_bytes(8,"little")+b"x")
            with self.assertRaises(WanCompatibilityError):
                check_small_safetensors_header(broken,expected_size=broken.stat().st_size)
            lnk=root/"link.safetensors"
            lnk.symlink_to(a)
            with self.assertRaises(WanCompatibilityError):
                check_small_safetensors_header(lnk,expected_size=len(content))


if __name__=="__main__":
    unittest.main()
