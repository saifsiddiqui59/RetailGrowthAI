"""Source-only F7/F2/F4 compatibility tripwire; no remote fetch or real approval.

This test checks F7's local handoff on every branch CI. F2/F4 checks run
only after their real modules exist in the same coordinator checkout; absence
is explicitly skipped, never interpreted as cross-feature integration success.
"""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
F7 = ROOT / "video-engine" / "feature7"
MANIFEST = F7 / "CROSS_FEATURE_CONTRACT_AUDIT_20261030.json"
F2_SOURCE = ROOT / "ai-agents" / "src" / "ai_agents" / "feature2_voice_quality.py"
F4_SOURCE = ROOT / "video-engine" / "feature4_edit_execution.py"


def _frozen_fields(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name
                   for target in node.targets):
            continue
        if (not isinstance(node.value, ast.Call)
                or not isinstance(node.value.func, ast.Name)
                or node.value.func.id != "frozenset"
                or len(node.value.args) != 1):
            raise AssertionError("Unexpected Feature4 contract field declaration")
        return set(ast.literal_eval(node.value.args[0]))
    raise AssertionError("Feature4 contract field declaration missing")


class Feature7CrossFeatureContractAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_local_feature7_review_and_original_wav_are_non_executable(self):
        audit = self.audit
        self.assertEqual(audit["schema"], "feature7_cross_feature_source_contract_audit_v1")
        self.assertEqual(audit["status"], "source_review_only_not_integrated")
        self.assertFalse(audit["feature7"]["approval_allowed"])
        self.assertFalse(audit["feature7"]["renderable"])
        self.assertFalse(audit["acceptance"]["real_cpu_asr_executed"])
        self.assertFalse(audit["acceptance"]["hosted_jwt_rls_verified"])
        self.assertFalse(audit["acceptance"]["final_render_verified"])
        wav = (F7 / "original_wav_cpu.mjs").read_text(encoding="utf-8")
        speech = (F7 / "feature4_speech_review_handoff.mjs").read_text(encoding="utf-8")
        self.assertIn(audit["feature7"]["original_wav_receipt_version"], wav)
        self.assertIn(audit["feature7"]["speech_review_bundle_version"], speech)
        self.assertIn("approved:false", speech)
        self.assertIn("renderable:false", speech)
        self.assertEqual(audit["feature2"]["expected_receipt_version"],
                         audit["feature7"]["original_wav_receipt_version"])
        self.assertFalse(audit["feature4"]["supports_sparse_multicut"])

    def test_actual_feature2_consumer_signature_when_present(self):
        if not F2_SOURCE.is_file():
            self.skipTest("F2 #551 source not yet in same coordinator checkout")
        source = F2_SOURCE.read_text(encoding="utf-8")
        names = {node.name for node in ast.parse(source).body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        f2 = self.audit["feature2"]
        self.assertIn(f2["consumer_function"], names)
        self.assertIn(f2["wer_consumer_function"], names)
        self.assertIn(f2["expected_receipt_version"], source)
        self.assertIn(f2["requires_original_audio_kind"], source)

    def test_actual_feature4_approved_edit_fields_when_present(self):
        if not F4_SOURCE.is_file():
            self.skipTest("F4 #322 source not yet in same coordinator checkout")
        source = F4_SOURCE.read_text(encoding="utf-8")
        f4 = self.audit["feature4"]
        names = {node.name for node in ast.parse(source).body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertIn(f4["approved_edit_function"], names)
        self.assertIn(f4["approved_timeline_version"], source)
        self.assertEqual(_frozen_fields(source, "EDIT_FIELDS"),
                         set(f4["approved_edit_fields"]))
        self.assertEqual(_frozen_fields(source, "EDIT_SCENE_FIELDS"),
                         set(f4["approved_scene_fields"]))
        self.assertIn("approved", f4["approved_edit_fields"])
        self.assertFalse(self.audit["feature7"]["approval_allowed"])


if __name__ == "__main__":
    unittest.main()
