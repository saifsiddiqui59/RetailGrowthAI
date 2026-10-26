"""FLUX GPU precision tests use fake CUDA/Diffusers: no model or GPU downloads."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import sys
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from gpu_worker_v2 import OfflineFluxKlein4B
from ai_providers_v2 import InferenceJob, ProviderBlocked

SHOP = "00000000-0000-4000-8000-000000000111"
JOB = "00000000-0000-4000-8000-000000000222"

class FakeGenerator:
    def __init__(self,device): self.device=device
    def manual_seed(self,seed): return self

class FakePipeline:
    used = None
    def __init__(self):
        self.cpu_offload=False
        self.cuda=False
    @classmethod
    def from_pretrained(cls,path,torch_dtype,local_files_only):
        assert local_files_only is True
        cls.used={"dtype":torch_dtype,"weights":path}
        return cls()
    def enable_model_cpu_offload(self): self.cpu_offload=True
    def to(self,device):
        self.cuda=device=="cuda"
        return self
    def __call__(self,**kw):
        self.args=kw
        return SimpleNamespace(images=[Image.new("RGB",(64,64),"white")])

class FluxT4Tests(unittest.TestCase):
    def make_modules(self,cap=(7,5),vram=16,bf16=False):
        torch=ModuleType("torch")
        torch.bfloat16="bf16"
        torch.float16="fp16"
        torch.Generator=FakeGenerator
        torch.cuda=SimpleNamespace(
            is_available=lambda:True,
            get_device_capability=lambda:cap,
            is_bf16_supported=lambda:bf16,
            get_device_properties=lambda idx:SimpleNamespace(total_memory=vram*1024**3),
            synchronize=lambda idx:None,
            max_memory_allocated=lambda idx:1024, # fake CUDA allocation evidence

        )
        diffusers=ModuleType("diffusers")
        diffusers.Flux2KleinPipeline=FakePipeline
        return {"torch":torch,"diffusers":diffusers}

    def test_t4_uses_fp16_cpu_offload_and_approved_offline_weights(self):
        with TemporaryDirectory() as tmp,patch.dict(sys.modules,self.make_modules()):
            worker=OfflineFluxKlein4B(tmp,height=512,width=512)
            png=worker(InferenceJob(SHOP,JOB,"human_model",prompt="adult clothing catalog"),{})
            self.assertTrue(png.startswith(b"\x89PNG"))
            self.assertTrue(worker.actual_cuda_verified) # fake torch only, not actual hardware acceptance
            self.assertEqual(FakePipeline.used["dtype"],"fp16")
            self.assertTrue(worker.pipeline.cpu_offload)
            self.assertFalse(worker.pipeline.cuda)
            self.assertEqual(worker.pipeline.args["num_inference_steps"],4)
            self.assertIn("adult",worker.pipeline.args["prompt"])
            self.assertTrue(FakePipeline.used["weights"].startswith("/"))

    def test_ampere_bf16_can_use_full_memory_path(self):
        with TemporaryDirectory() as tmp,patch.dict(sys.modules,self.make_modules(cap=(8,6),vram=24,bf16=True)):
            worker=OfflineFluxKlein4B(tmp)
            worker(InferenceJob(SHOP,JOB,"text_to_image",prompt="summer product photo"),{})
            self.assertEqual(FakePipeline.used["dtype"],"bf16")
            self.assertTrue(worker.pipeline.cuda)
            self.assertFalse(worker.pipeline.cpu_offload)

    def test_cuda_allocation_must_be_real_before_attestation(self):
        fake=self.make_modules()
        fake["torch"].cuda.max_memory_allocated=lambda idx:0
        with TemporaryDirectory() as tmp,patch.dict(sys.modules,fake):
            worker=OfflineFluxKlein4B(tmp,height=512,width=512)
            with self.assertRaisesRegex(ProviderBlocked, "did not allocate device memory"):
                worker(InferenceJob(SHOP,JOB,"human_model",prompt="adult fashion item"),{})
            self.assertFalse(worker.actual_cuda_verified)

    def test_bad_cuda_and_under_14gb_rejected_before_loading_model(self):
        for cap,vram in (((6,0),16),((7,5),12)):
            with self.subTest(cap=cap,vram=vram):
                with TemporaryDirectory() as tmp,patch.dict(sys.modules,self.make_modules(cap=cap,vram=vram)):
                    with self.assertRaises(ProviderBlocked):
                        OfflineFluxKlein4B(tmp)(InferenceJob(SHOP,JOB,"human_model",prompt="adult"),{})

if __name__=="__main__":unittest.main()
