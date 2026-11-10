"""GPU-OFF ComfyUI native graph tests; no CUDA, model, or HTTP usage."""
import unittest
from feature5_motion.infra.feature35_comfy_api_graphs import (
    flux_klein_4b, wan22_ti2v_5b, offline_graph_validate, WorkflowError,
)


class TestFeature35HeadlessGraphs(unittest.TestCase):
    def test_flux_distilled_native_staged_checkpoints(self):
        graph=flux_klein_4b(prompt="An adult in a blue festive kurti, realistic cloth",seed=42)
        self.assertGreater(offline_graph_validate(graph), 10)
        n=graph["prompt"]
        self.assertEqual(n["1"]["inputs"]["unet_name"],"flux-2-klein-4b.safetensors")
        self.assertEqual(n["2"]["inputs"]["clip_name"],"qwen_3_4b.safetensors")
        self.assertEqual(n["2"]["inputs"]["type"],"flux2")
        self.assertEqual(n["3"]["inputs"]["vae_name"],"flux2-vae.safetensors")
        self.assertEqual(n["10"]["inputs"]["steps"],4)
        self.assertNotIn("16",n)
        self.assertFalse(any("fp8.safetensors" in str(v) for v in n.values()))

    def test_flux_reference_edit_uses_one_authorized_staged_basename(self):
        graph=flux_klein_4b(prompt="Preserve this garment, adjust ambient lighting",seed=43,approved_input_file="owned_asset_001.png")
        self.assertGreater(offline_graph_validate(graph), 13)
        n=graph["prompt"]
        self.assertEqual(n["16"]["inputs"]["image"],"owned_asset_001.png")
        self.assertEqual(n["18"]["class_type"],"ReferenceLatent")
        self.assertEqual(n["6"]["inputs"]["positive"],["18",0])

    def test_wan_t2v_and_i2v_native_hybrid(self):
        for filename in (None,"owned_motion_source.webp"):
            with self.subTest(filename=filename):
                n=wan22_ti2v_5b(prompt="Adult model walks forward, soft lighting, no text",seed=7,
                                approved_input_file=filename)["prompt"]
                self.assertGreaterEqual(offline_graph_validate({"prompt":n}),11)
                self.assertEqual(n["1"]["inputs"]["unet_name"],"wan2.2_ti2v_5B_fp16.safetensors")
                self.assertEqual(n["2"]["inputs"]["clip_name"],"umt5_xxl_fp8_e4m3fn_scaled.safetensors")
                self.assertEqual(n["3"]["inputs"]["vae_name"],"wan2.2_vae.safetensors")
                self.assertEqual(n["7"]["inputs"]["length"],121)
                self.assertEqual(n["11"]["inputs"]["fps"],24)
                self.assertNotIn("start_image",n["7"]["inputs"]) if filename is None else self.assertEqual(n["7"]["inputs"]["start_image"],["6",0])

    def test_security_rejects_foreign_path_and_invalid_bounds(self):
        rejected=("tenant/a.png","../foreign.png","http://url.png","unsafe.webp/../thing.png")
        for input_name in rejected:
            with self.subTest(input_name=input_name),self.assertRaises(WorkflowError):
                flux_klein_4b(prompt="Fashion",seed=1,approved_input_file=input_name)
            with self.subTest(wan=input_name),self.assertRaises(WorkflowError):
                wan22_ti2v_5b(prompt="Fashion",seed=1,approved_input_file=input_name)
        for keyword in ({"seed":-1},{"width":9999},{"output_prefix":"../other"},{"prompt":""}):
            args={"prompt":"text","seed":0,**keyword}
            with self.assertRaises(WorkflowError): flux_klein_4b(**args)
        for kwargs in ({"frames":120},{"fps":30},{"height":710},{"seed":-5},
                       {"width":832,"height":480},{"width":1080,"height":1920}):
            with self.assertRaises(WorkflowError): wan22_ti2v_5b(**{"prompt":"text","seed":1,**kwargs})

    def test_broken_internal_link_is_rejected_offline(self):
        g=wan22_ti2v_5b(prompt="A fictional boutique at sunset",seed=0)
        g["prompt"]["9"]["inputs"]["latent_image"]=["bad-node",0]
        with self.assertRaises(WorkflowError): offline_graph_validate(g)
