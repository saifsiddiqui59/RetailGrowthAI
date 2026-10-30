"""Offline Feature #4 authoring, authorization and source-audio regression tests.

These are compiler/unit tests; they do not assert a HyperFrames video was rendered.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from professional import (
    VideoPlanError, compile_composition, validate,
    SUPPORTED_ANIMATIONS, SUPPORTED_TRANSITIONS,
)  # noqa: E402
from creative_contract import ANIMATIONS, TRANSITIONS  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
RIGHTS = {"commercial_use": True, "license": "owned", "evidence": "Fixture author grant",
          "source": "original test pattern authored in CI"}


class ProfessionalVideoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / "authorized"
        self.media.mkdir()
        self.output = self.root / "project"
        self.manifest = {"shop_id": SHOP, "assets": {}}
        self.plan = {
            "version": "rg_video_v2", "shop_id": SHOP, "mode": "text",
            "template": "streetwear", "duration_seconds": 15,
            "output": {"width": 540, "height": 960, "fps": 24},
            "scenes": [
                {"start": 0, "duration": 5, "headline": "OUR NEW SEASON"},
                {"start": 5, "duration": 5, "headline": "Hand-picked style"},
                {"start": 10, "duration": 5, "headline": "The Boutique"},
            ],
            "cta": "Visit our shop",
        }

    def image(self):
        # Real small staged PNG; the compiler's ffprobe preflight remains active.
        p = self.media / "product.png"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "color=c=red:s=128x128:d=1",
                        "-frames:v", "1", "-update", "1", str(p)],
                       check=True, capture_output=True, timeout=20)
        self.manifest["assets"]["photo1"] = {"kind": "image", "path": "product.png",
                                              "rights": copy.deepcopy(RIGHTS)}
        for s in self.plan["scenes"]:
            s["asset_id"] = "photo1"

    def audio(self):
        p = self.media / "music.wav"
        with wave.open(str(p), "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            for _ in range(15):
                wav.writeframes(b"\x00\x00\x00\x00" * 44100)
        self.manifest["assets"]["music1"] = {"kind": "audio", "path": "music.wav",
                                              "rights": copy.deepcopy(RIGHTS)}
        self.plan["music_asset_id"] = "music1"

    def test_mode_a_text_to_video_compiles_offline(self):
        output = compile_composition(self.plan, self.manifest, self.media, self.output)
        page = (output / "index.html").read_text()
        self.assertIn('data-composition-id="main"', page)
        self.assertIn('data-no-timeline', page)
        self.assertIn("OUR NEW SEASON", page)
        self.assertNotIn("<script", page)
        self.assertTrue((output / "assets/silence.wav").is_file())
        self.assertEqual(json.loads((output / "render-config.json").read_text())["renderer"], "hyperframes")

    def test_full_hd_compiler_records_exact_dimensions_and_fps(self):
        self.plan["output"] = {"width": 1080, "height": 1920, "fps": 30}
        output = compile_composition(self.plan, self.manifest, self.media, self.output)
        config = json.loads((output / "render-config.json").read_text())
        page = (output / "index.html").read_text()
        self.assertEqual((config["width"], config["height"], config["fps"]),
                         (1080, 1920, 30))
        self.assertIn('data-width="1080" data-height="1920"', page)
        self.assertIn('data-fps="30"', page)
        self.assertIn("role-intro", page)
        self.assertIn("role-outro", page)
        # On portrait export the product artwork must stop before the lower-third copy.
        self.assertIn(".role-product .photo-wrap{top:6%;height:66%", page)

    def test_all_supported_editor_effects_compile_to_actual_css_keyframes(self):
        """F4-05 source parity; no fake encoded-video/Chromium frame claim."""
        self.assertEqual(ANIMATIONS, SUPPORTED_ANIMATIONS)
        self.assertEqual(TRANSITIONS, SUPPORTED_TRANSITIONS)
        animations = ("subtle_zoom", "fade", "slide", "pop", "glow")
        transitions = ("fade", "slide", "cut")
        self.plan["scenes"] = [{
            "start": i * 3, "duration": 3, "headline": f"REVIEWED SCENE {i}",
            "animation_preset": preset,
            "transition": transitions[i % len(transitions)],
        } for i, preset in enumerate(animations)]
        output = compile_composition(self.plan, self.manifest, self.media, self.output)
        page = (output / "index.html").read_text(encoding="utf-8")
        for preset in animations:
            with self.subTest(preset=preset):
                self.assertIn(f"anim-{preset}", page)
        for transition in transitions:
            with self.subTest(transition=transition):
                self.assertIn(f"trans-{transition}", page)
        for keyframe in ("presetSubtleZoom", "presetFade", "presetSlide",
                         "presetGlow", "promoPop", "editorialFade", "editorialSlide"):
            with self.subTest(keyframe=keyframe):
                self.assertIn(f"@keyframes {keyframe}", page)
        for selector in (".anim-subtle_zoom .glass{animation:presetSubtleZoom",
                         ".anim-fade .glass{animation:presetFade",
                         ".anim-slide .glass{animation:presetSlide",
                         ".anim-pop .glass{animation:promoPop",
                         ".anim-glow .glass{animation:presetGlow",
                         ".scene.trans-fade{animation:editorialFade",
                         ".scene.trans-slide{animation:editorialSlide",
                         ".scene.trans-cut{animation:none"):
            with self.subTest(selector=selector):
                self.assertIn(selector, page)
        self.assertNotIn("<script", page)

    def test_unsupported_effects_are_rejected_before_compilation(self):
        for name, value in (("animation_preset", "3d_rotate"),
                            ("animation_preset", "fade;position:absolute"),
                            ("transition", "glitch"),
                            ("transition", "slide;opacity:0")):
            with self.subTest(name=name, value=value):
                trial = copy.deepcopy(self.plan)
                trial["scenes"][0][name] = value
                with self.assertRaisesRegex(VideoPlanError, "Unknown"):
                    validate(trial, self.manifest, self.media)

    def test_sixty_second_script_acceptance_without_expensive_render(self):
        self.plan["duration_seconds"] = 60
        for index, scene in enumerate(self.plan["scenes"]):
            scene["start"] = index * 20
            scene["duration"] = 20
        ordered, has_source_audio = validate(self.plan, self.manifest, self.media)
        self.assertEqual(ordered, {})
        self.assertFalse(has_source_audio)

    def test_mode_b_image_to_video_reuses_actual_media(self):
        self.image()
        self.plan["mode"] = "image"
        output = compile_composition(self.plan, self.manifest, self.media, self.output)
        page = (output / "index.html").read_text()
        self.assertIn("assets/asset00.png", page)
        self.assertEqual(page.count('<img class="product-photo"'), 3)
        self.assertEqual(len(list((output / "assets").glob("*.png"))), 1)

    def test_mode_c_poster_to_video_retains_approved_offer(self):
        self.image()
        self.manifest["assets"]["photo1"]["kind"] = "poster"
        self.plan["mode"] = "poster"
        self.plan["template"] = "festival"
        self.plan["scenes"][1]["offer"] = "20% OFF"
        page = (compile_composition(self.plan, self.manifest, self.media, self.output) /
                "index.html").read_text()
        self.assertIn("20% OFF", page)
        self.assertIn("CELEBRATE IN STYLE", page)

    def test_mode_d_media_supports_scene_order(self):
        self.image()
        self.plan["mode"] = "media"
        self.plan["template"] = "cinematic"
        page = (compile_composition(self.plan, self.manifest, self.media, self.output) /
                "index.html").read_text()
        self.assertLess(page.index("OUR NEW SEASON"), page.index("Hand-picked style"))
        self.assertIn("THE COLLECTION", page)

    def test_mode_e_beat_grid_requires_music_and_alignment(self):
        self.image()
        self.audio()
        self.plan["mode"] = "music_sync"
        self.plan["beats"] = [0, 5, 10, 14]
        output = compile_composition(self.plan, self.manifest, self.media, self.output)
        self.assertIn('data-volume="0.55"', (output / "index.html").read_text())
        self.assertFalse((output / "assets/silence.wav").exists())
        self.plan["beats"] = [0, 4, 9, 14]
        with self.assertRaisesRegex(VideoPlanError, "align"):
            validate(self.plan, self.manifest, self.media)

    def test_cross_shop_and_rights_revocation_rejected(self):
        self.image()
        self.manifest["shop_id"] = OTHER
        with self.assertRaisesRegex(VideoPlanError, "shop_id"):
            validate(self.plan, self.manifest, self.media)
        self.manifest["shop_id"] = SHOP
        self.manifest["assets"]["photo1"]["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(ValueError, "commercial-use"):
            validate(self.plan, self.manifest, self.media)

    def test_html_injection_escaped_and_template_expression_denied(self):
        self.plan["scenes"][0]["headline"] = '<img src="http://attack" onerror="alert(1)">'
        page = (compile_composition(self.plan, self.manifest, self.media, self.output) /
                "index.html").read_text()
        self.assertNotIn('<img src="http:', page)
        self.assertIn("&lt;img", page)
        self.plan["js"] = "process.exit()"
        with self.assertRaisesRegex(VideoPlanError, "unsupported"):
            validate(self.plan, self.manifest, self.media)

    def test_traversal_and_remote_urls_rejected(self):
        self.image()
        self.manifest["assets"]["photo1"]["path"] = "../outside.png"
        with self.assertRaises((ValueError, FileNotFoundError)):
            validate(self.plan, self.manifest, self.media)
        self.manifest["assets"]["photo1"]["path"] = "https://evil.invalid/a.png"
        with self.assertRaisesRegex(ValueError, "server-staged"):
            validate(self.plan, self.manifest, self.media)

    def test_no_gaps_boolean_durations_or_unbounded_output(self):
        self.plan["scenes"][1]["start"] = 6
        with self.assertRaisesRegex(VideoPlanError, "contiguous"):
            validate(self.plan, self.manifest, self.media)
        self.plan["scenes"][1]["start"] = 5
        self.plan["scenes"][1]["duration"] = True
        with self.assertRaisesRegex(VideoPlanError, "finite"):
            validate(self.plan, self.manifest, self.media)
        self.plan["scenes"][1]["duration"] = 5
        self.plan["output"]["width"] = 8192
        with self.assertRaisesRegex(VideoPlanError, "portrait"):
            validate(self.plan, self.manifest, self.media)

    def test_source_video_voice_is_not_muted_by_default(self):
        file = self.media / "shop.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "color=c=blue:s=120x200:r=12:d=15",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=15",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest", str(file)],
                       check=True, capture_output=True, timeout=40)
        self.manifest["assets"]["clip1"] = {"kind": "video", "path": "shop.mp4",
                                             "rights": copy.deepcopy(RIGHTS)}
        self.plan["mode"] = "media"
        self.plan["scenes"] = [{"start": 0, "duration": 15, "headline": "Store tour", "asset_id": "clip1"}]
        self.audio()
        page = (compile_composition(self.plan, self.manifest, self.media, self.output) /
                "index.html").read_text()
        self.assertIn('<video class="footage clip"', page)
        self.assertIn('data-has-audio="true"', page)
        self.assertNotIn('playsinline muted', page)
        self.assertIn('data-volume="0.12"', page)
        self.assertIn('id="soundtrack0"', page)
        self.assertIn('data-media-start="0"', page)


if __name__ == "__main__":
    unittest.main()
