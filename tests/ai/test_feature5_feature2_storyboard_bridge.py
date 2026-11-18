"""Feature5 GPU-off validation of Feature2's versioned MIT export shape.

Fixture resembles the actual PR #551 exporter schema using the already
established F5 motion-direction fixture. The Feature2 Node exporter is still
an unmerged draft, so these are consumer-contract tests, not an execution of
the exporter or proof of a signed customer creative approval.
"""
import copy
from hashlib import sha256
import unittest

from feature5_motion.feature2_storyboard_bridge import qualify_feature2_offline_storyboard
from feature5_motion.wan22_motion_adapter import PROVIDER, WanCompatibilityError
from test_feature5_wan22_motion_adapter import fixture


def make_packet(duration=15):
    dispatch, _, _, _ = fixture()
    base = dispatch["shot"]
    source_shop, source_campaign = base["shop_id"], base["campaign_id"]
    facts = base["garment_lock"]
    shots, timeline, cues = [], [], []
    for index in range(duration // 5):
        direction = copy.deepcopy(base)
        direction["scene_id"] = "scene-" + str(index)
        direction["shot_id"] = "shot-" + str(index)
        direction["shot_start_seconds"] = index * 5
        direction["generation_prompt"] += " The straight hem stays unchanged in every frame."
        digest = sha256(direction["generation_prompt"].encode()).hexdigest()
        shots.append({
            "shot_id": direction["shot_id"], "scene_id": direction["scene_id"],
            "start_seconds": index * 5, "duration_seconds": 5,
            "original_direction": direction, "original_prompt_sha256": digest,
            "first_frame_asset_id": None, "first_frame_sha256": None,
            "native_wan_profile": {"model": PROVIDER, "width": 704,
                                   "height": 1280, "fps": 24, "frames": 121},
            "provider_call_permitted": False, "gpu_enabled": False,
            "cost_reserved": False, "ready_for_feature5_lease": False,
        })
        timeline.append({
            "shot_id": direction["shot_id"], "scene_id": direction["scene_id"],
            "start_seconds": index * 5, "duration_seconds": 5,
            "immutable_motion_prompt_sha256": digest,
            "garment_lock": copy.deepcopy(facts),
            "camera": copy.deepcopy(direction["camera"]), "lighting": direction["lighting"],
            "asset_id": None, "ready_to_render": False,
        })
        cues.append({
            "shot_id": direction["shot_id"], "start_seconds": index * 5,
            "duration_seconds": 5, "voiceover_text": "Synthetic cue",
            "real_speech_audio_verified": False,
        })
    # Recreate the actual Feature2 director's prev/next linked shot chain,
    # rather than letting a contract-shaped fixture hide missing continuity.
    for i, request in enumerate(shots):
        direction = request["original_direction"]
        direction["previous_shot_id"] = shots[i - 1]["shot_id"] if i else None
        direction["next_shot_id"] = (shots[i + 1]["shot_id"]
                                     if i + 1 < len(shots) else None)
    return {
        "schema": "retailgrowth.feature2-f4-f5-offline-fixture.v1",
        "source_engine": "pinned MIT Kuble-Lab Open Creative Director",
        "shop_id": "SYNTHETIC_NOT_REAL_OWNER",
        "original_fixture_shop_id": source_shop,
        "original_fixture_campaign_id": source_campaign,
        "source_plan_sha256": "b" * 64,
        "duration_seconds": duration,
        "garment_facts": copy.deepcopy(facts),
        "source_media": {
            "approved_feature3_frame_present": False,
            "candidates": [{
                "id": "test-stock", "sha256": None, "private_asset_id": None,
                "can_claim_retailer_product": False,
            }],
        },
        "feature4": {
            "target": {"width": 1080, "height": 1920, "fps": 24,
                       "video_codec": "h264", "audio_codec": "aac"},
            "timeline": timeline, "approved_render_request": None,
            "ready_to_render_customer_reel": False,
        },
        "feature5": {
            "native_output_not_full_hd": True, "clip_requests": shots,
            "can_run_paid_motion": False,
            "approved_feature3_first_frame_present": False, "gpu_enabled": False,
        },
        "audio": {
            "narration_cues": cues, "licensed_music_bytes_present": False,
            "voiceover_audio_bytes_present": False,
        },
        "review": {
            "status": "SYNTHETIC_DRAFT", "signed_customer_approval": False,
            "licensed_media_approval": False, "approved_product_or_model": False,
            "owner_confirmed_offer": False, "can_publish": False,
            "paid_calls": 0, "hosted_reel_rendered": False,
        },
    }


class Feature2F5SourceContractTests(unittest.TestCase):
    def test_all_15_30_60_second_shot_sequences_are_source_only(self):
        for duration in (15, 30, 60):
            with self.subTest(duration=duration):
                source = make_packet(duration)
                record = qualify_feature2_offline_storyboard(source)
                self.assertEqual(record["segment_count"], duration // 5)
                self.assertEqual(record["duration_seconds"], duration)
                self.assertFalse(record["can_submit_provider"])
                self.assertFalse(record["can_publish"])
                self.assertFalse(record["approved_for_feature4"])
                self.assertEqual([row["start_seconds"] for row in record["segments"]],
                                 list(range(0, duration, 5)))
                self.assertEqual(record, qualify_feature2_offline_storyboard(source))

    def test_stale_prompt_garment_timeline_and_shop_rejected(self):
        mutators = [
            lambda p: p["feature5"]["clip_requests"][1].update(
                original_prompt_sha256="c" * 64),
            lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                generation_prompt="tampered creative"),
            lambda p: p["garment_facts"].update(embroidery="different embroidery"),
            lambda p: p["feature4"]["timeline"][1].update(start_seconds=0),
            lambda p: p["feature4"]["timeline"][0].update(
                immutable_motion_prompt_sha256="f" * 64),
            lambda p: p["feature5"]["clip_requests"][2]["original_direction"].update(
                shop_id="foreign"),
            lambda p: p["feature4"]["timeline"][1].update(
                camera={"movement": "rewritten"}),
            lambda p: p["feature5"]["clip_requests"][1].update(
                shot_id=p["feature5"]["clip_requests"][0]["shot_id"]),
        ]
        for change in mutators:
            packet = make_packet(15)
            change(packet)
            with self.subTest(change=str(change)), self.assertRaises(WanCompatibilityError):
                qualify_feature2_offline_storyboard(packet)

    def test_linked_storyboard_and_product_identity_must_survive_edits(self):
        for duration in (15, 30, 60):
            original = make_packet(duration)
            self.assertEqual(qualify_feature2_offline_storyboard(original)["segment_count"],
                             duration // 5)
            mutations = [
                lambda p: p["feature5"]["clip_requests"][0]["original_direction"].update(
                    next_shot_id=None),
                lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                    previous_shot_id="shot-999"),
                lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                    reference_media_id="different-garment"),
                lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                    product_sku="NEW-SKU"),
                lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                    reference_facts_sha256="f" * 64),
                lambda p: p["feature5"]["clip_requests"][1]["original_direction"][
                    "garment_lock"].update(unapproved_fabric="synthetic leather"),
                lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                    scene_id=p["feature5"]["clip_requests"][0]["scene_id"]),
            ]
            for mutate in mutations:
                p = copy.deepcopy(original)
                mutate(p)
                with self.subTest(duration=duration, mutation=str(mutate)):
                    with self.assertRaises(WanCompatibilityError):
                        qualify_feature2_offline_storyboard(p)

    def test_never_promote_unregistered_media_gpu_credits_or_review(self):
        mutators = [
            lambda p: p["feature5"].update(can_run_paid_motion=True),
            lambda p: p["feature5"].update(gpu_enabled=True),
            lambda p: p["review"].update(signed_customer_approval=True),
            lambda p: p["review"].update(can_publish=True),
            lambda p: p["review"].update(paid_calls=1),
            lambda p: p["source_media"].update(approved_feature3_frame_present=True),
            lambda p: p["feature5"]["clip_requests"][0].update(cost_reserved=True),
            lambda p: p["feature5"]["clip_requests"][0].update(
                first_frame_asset_id="pretend-id"),
            lambda p: p["feature5"]["clip_requests"][0].update(
                native_wan_profile={"model": "hunyuanvideo-1.5-480p"}),
            lambda p: p["feature4"]["timeline"][0].update(ready_to_render=True),
            lambda p: p["audio"].update(licensed_music_bytes_present=True),
            lambda p: p["audio"]["narration_cues"][0].update(real_speech_audio_verified=True),
            lambda p: p["source_media"]["candidates"][0].update(
                private_asset_id="pretend-asset"),
        ]
        for change in mutators:
            packet = make_packet(30)
            change(packet)
            with self.subTest(change=str(change)), self.assertRaises(WanCompatibilityError):
                qualify_feature2_offline_storyboard(packet)

    def test_original_director_timing_requires_exact_integer_types(self):
        # Python considers False == 0 and 5.0 == 5; a signed director
        # timeline must not accept these ambiguous serialized JSON types.
        for index, field, value in (
            (0, "shot_start_seconds", False),
            (0, "shot_start_seconds", 0.0),
            (1, "shot_start_seconds", 5.0),
            (0, "duration_seconds", 5.0),
        ):
            packet = make_packet(15)
            packet["feature5"]["clip_requests"][index]["original_direction"][field] = value
            with self.subTest(index=index, field=field, value=value):
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature2_offline_storyboard(packet)

    def test_matched_but_malformed_camera_or_lighting_is_denied(self):
        # Comparing F4 and F5 by equality alone is insufficient: a forged
        # source could give both consumers the same invalid camera values.
        for field, value in (
            ("camera", {"movement": "pan"}),
            ("camera", {"framing": 42, "lens": "50mm",
                        "composition": "center", "movement": "pan"}),
            ("lighting", None),
            ("lighting", "  "),
        ):
            packet = make_packet(15)
            direction = packet["feature5"]["clip_requests"][0]["original_direction"]
            timeline = packet["feature4"]["timeline"][0]
            direction[field] = copy.deepcopy(value)
            timeline[field] = copy.deepcopy(value)
            with self.subTest(field=field, value=value):
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature2_offline_storyboard(packet)

    def test_reject_noncontiguous_and_unsupported_durations(self):
        for duration in (5, 10, 25, 20, 90, True):
            packet = make_packet(15)
            packet["duration_seconds"] = duration
            with self.subTest(duration=duration), self.assertRaises(WanCompatibilityError):
                qualify_feature2_offline_storyboard(packet)
        packet = make_packet(60)
        packet["feature5"]["clip_requests"].pop()
        with self.assertRaises(WanCompatibilityError):
            qualify_feature2_offline_storyboard(packet)


if __name__ == "__main__":
    unittest.main()
