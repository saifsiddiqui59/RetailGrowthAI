"""F4-15 trusted AI edit execution: CPU-only, synthetic approval fixtures.

These tests do NOT run AI, certify a real commercial video or authenticate a
hosted Azure request. Feature #7 must supply independently verified decisions.
"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))

from creative_contract import CreativeContractError, render_inputs
from feature4_edit_execution import (
    draft_fingerprint, edit_decision_fingerprint, execute_approved_edit,
)
from test_feature4_intent_compiler import pair, OTHER


def reviewed_pair():
    draft, trusted = pair()
    trusted["edit_plan"] = {
        "source_feature": "feature7", "approved": True,
        "approval_id": "approved-feature7-timeline-001",
        "timeline_version": "creative_reel_v1",
    }
    edits = {
        **trusted["edit_plan"],
        "shop_id": trusted["shop_id"],
        "campaign_id": trusted["campaign_id"],
        "draft_sha256": draft_fingerprint(draft),
        "scenes": [
            {"source_scene_index": 1, "duration": 9,
             "trim_start": 1.5, "mute_source": False,
             "transition": "cut", "animation_preset": "fade"},
            {"source_scene_index": 0, "duration": 11,
             "animation_preset": "slide", "transition": "fade"},
            {"source_scene_index": 2, "duration": 10,
             "animation_preset": "pop", "transition": "cut"},
        ],
    }
    trusted["edit_decision_sha256"] = edit_decision_fingerprint(edits)
    return draft, trusted, edits


class TrustedEditExecutionTests(unittest.TestCase):
    def test_real_renderer_plan_receives_approved_cut_order_and_timing(self):
        draft, trusted, edits = reviewed_pair()
        original = copy.deepcopy(draft)
        result = execute_approved_edit(draft, trusted, edits)
        request = result["request"]
        self.assertEqual([s["asset_id"] for s in request["scenes"]],
                         ["motionwalk", "photokurti", "photokurti"])
        self.assertEqual([s["start_time"] for s in request["scenes"]], [0, 9, 20])
        self.assertEqual([s["duration"] for s in request["scenes"]], [9, 11, 10])
        self.assertEqual(request["scenes"][0]["trim_start"], 1.5)
        self.assertEqual(request["scenes"][0]["transition"], "cut")
        self.assertFalse(request["scenes"][0]["mute_source"])
        self.assertEqual(request["scenes"][1]["animation_preset"], "slide")
        self.assertEqual(request["scenes"][2]["text_overlay"], "20% OFF")
        self.assertEqual(request["script"]["cta"], "Visit Our Store")
        self.assertEqual(request["edit_plan"], trusted["edit_plan"])
        self.assertNotIn("edit_decision_sha256", request)
        self.assertEqual(
            trusted["edit_decision_sha256"], edit_decision_fingerprint(edits))
        self.assertEqual(result["lineage"]["source_edit_approval"],
                         "approved-feature7-timeline-001")
        lowered = render_inputs(request, result["manifest"])
        self.assertEqual(lowered.audit, result["lineage"])
        self.assertEqual([s["start"] for s in lowered.plan["scenes"]], [0, 9, 20])
        self.assertEqual([s["duration"] for s in lowered.plan["scenes"]], [9, 11, 10])
        self.assertEqual([s["asset_id"] for s in lowered.plan["scenes"]],
                         ["motionwalk", "photokurti", "photokurti"])
        self.assertEqual(lowered.plan["scenes"][0]["transition"], "cut")
        self.assertEqual(lowered.plan["scenes"][0]["trim_start"], 1.5)
        self.assertEqual(draft, original, "original reviewed draft must remain immutable")
        self.assertEqual(set(result["manifest"]["assets"]),
                         {"photokurti", "motionwalk", "saleposter",
                          "musicowned", "storelogo"})

    def test_unapproved_or_foreign_editor_receipt_fails_closed(self):
        cases = [
            ("wrong feature", lambda d,s,e: e.update(source_feature="feature5")),
            ("unsigned decision", lambda d,s,e: e.update(approved=False)),
            ("wrong contract", lambda d,s,e: e.update(timeline_version="html")),
            ("foreign shop", lambda d,s,e: e.update(shop_id=OTHER)),
            ("foreign campaign", lambda d,s,e: e.update(campaign_id=OTHER)),
            ("foreign draft", lambda d,s,e: d.update(shop_id=OTHER)),
            ("forged reviewer", lambda d,s,e: e.update(approval_id="new-reviewer")),
            ("revoked reviewer", lambda d,s,e: s["edit_plan"].update(approved=False)),
            ("missing review", lambda d,s,e: s.pop("edit_plan")),
            ("invalid sha", lambda d,s,e: e.update(draft_sha256="abc")),
            ("stale sha", lambda d,s,e: e.update(draft_sha256="f" * 64)),
            ("missing persisted decision", lambda d,s,e: s.pop("edit_decision_sha256")),
            ("forged persisted decision", lambda d,s,e: s.update(edit_decision_sha256="f" * 64)),
            ("reordered without reapproval", lambda d,s,e: e["scenes"].reverse()),
            ("altered trim without reapproval", lambda d,s,e: e["scenes"][0].update(trim_start=2.5)),
            ("altered duration without reapproval", lambda d,s,e: e["scenes"][0].update(duration=8)),
            ("unknown instruction", lambda d,s,e: e.update(shell="rm -rf /")),
            ("source changed", lambda d,s,e: d["scenes"][1].update(asset_id="another")),
        ]
        for name, change in cases:
            draft, trusted, edits = reviewed_pair()
            change(draft, trusted, edits)
            with self.subTest(name=name), self.assertRaises(CreativeContractError):
                execute_approved_edit(draft, trusted, edits)

    def test_approved_review_digest_covers_every_edit_and_is_not_renderer_metadata(self):
        draft, trusted, edits = reviewed_pair()
        original_snapshot = copy.deepcopy(trusted)
        first = execute_approved_edit(draft, trusted, edits)
        self.assertEqual(trusted, original_snapshot)
        self.assertNotIn("edit_decision_sha256", first["request"]["edit_plan"])

        # An independently reviewed *new* trim is allowed when the persisted
        # server receipt is replaced; merely replaying the old ID is not.
        edits["scenes"][0]["trim_start"] = 2.5
        with self.assertRaisesRegex(CreativeContractError, "persisted review"):
            execute_approved_edit(draft, trusted, edits)
        trusted["edit_decision_sha256"] = edit_decision_fingerprint(edits)
        revised = execute_approved_edit(draft, trusted, edits)
        self.assertEqual(revised["request"]["scenes"][0]["trim_start"], 2.5)

    def test_invalid_or_dangerous_edit_commands_fail_closed(self):
        cases = [
            ("duplicate index", lambda e: e["scenes"][1].update(source_scene_index=1)),
            ("index string", lambda e: e["scenes"][1].update(source_scene_index="0")),
            ("missing scene", lambda e: e["scenes"].pop()),
            ("extra scene", lambda e: e["scenes"].append(copy.deepcopy(e["scenes"][0]))),
            ("negative", lambda e: e["scenes"][0].update(duration=-1)),
            ("nan", lambda e: e["scenes"][0].update(duration=float("nan"))),
            ("boolean duration", lambda e: e["scenes"][0].update(duration=True)),
            ("short timeline", lambda e: e["scenes"][0].update(duration=8)),
            ("invalid animation", lambda e: e["scenes"][0].update(animation_preset="eval")),
            ("invalid transition", lambda e: e["scenes"][0].update(transition="<script>")),
            ("unknown field", lambda e: e["scenes"][0].update(asset_id="fake")),
            ("negative trim", lambda e: e["scenes"][0].update(trim_start=-1)),
            ("infinite trim", lambda e: e["scenes"][0].update(trim_start=float("inf"))),
            ("audio string", lambda e: e["scenes"][0].update(mute_source="false")),
        ]
        for name, change in cases:
            draft, trusted, edits = reviewed_pair()
            change(edits)
            # Independently persisted approval can be validly bound to a
            # malformed decision; still test downstream schema rejection.
            with self.subTest(name=name), self.assertRaises(CreativeContractError):
                trusted["edit_decision_sha256"] = edit_decision_fingerprint(edits)
                execute_approved_edit(draft, trusted, edits)

    def test_existing_compiler_rejects_retimed_image_trim_or_forged_offer(self):
        draft, trusted, edits = reviewed_pair()
        edits["scenes"][1]["trim_start"] = 2
        trusted["edit_decision_sha256"] = edit_decision_fingerprint(edits)
        with self.assertRaisesRegex(CreativeContractError, "Trimming requires"):
            execute_approved_edit(draft, trusted, edits)

        draft, trusted, edits = reviewed_pair()
        draft["scenes"][2]["offer"] = "95% OFF"
        edits["draft_sha256"] = draft_fingerprint(draft)
        trusted["edit_decision_sha256"] = edit_decision_fingerprint(edits)
        with self.assertRaisesRegex(CreativeContractError, "Unreviewed promotional offer"):
            execute_approved_edit(draft, trusted, edits)

    def test_existing_compiler_rechecks_private_media_tenant_and_rights(self):
        for name, change in [
            ("foreign motion", lambda s: s["assets"]["motionwalk"].update(shop_id=OTHER)),
            ("revoked clip", lambda s: s["assets"]["motionwalk"].update(approved=False)),
            ("unlicensed music", lambda s: s["assets"]["musicowned"].update(license_name="unknown")),
            ("public storage", lambda s: s["assets"]["photokurti"].update(storage_bucket="public")),
        ]:
            draft, trusted, edits = reviewed_pair()
            change(trusted)
            with self.subTest(name=name), self.assertRaises(CreativeContractError):
                execute_approved_edit(draft, trusted, edits)


if __name__ == "__main__":
    unittest.main()
