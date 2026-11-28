"""Static original-Flex source compatibility checks, not a hosted release."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "f4_legacy_bindings", ROOT / "scripts/deploy/feature4_original_source_contract.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SOURCE = m.SOURCE.read_text(encoding="utf-8")
MANIFEST = json.loads(m.MANIFEST.read_text(encoding="utf-8"))


class OriginalSourceContract(unittest.TestCase):
    def test_current_source_preserves_all_legacy_and_f4_bindings(self):
        result = m.verify(SOURCE, MANIFEST)
        self.assertEqual(result["legacy_bindings_preserved"], 24)
        self.assertEqual(result["required_feature4_http_bindings"], 7)
        self.assertEqual(result["original_worker_bindings"], 9)
        self.assertFalse(result["restore_proved"])
        self.assertFalse(result["deployment_permitted"])

    def test_missing_route_changed_http_method_queue_and_added_worker_denied(self):
        changes = [
            SOURCE.replace("def create_feature4_render(", "def removed_f4(", 1),
            SOURCE.replace('route="campaigns", methods=["POST"]',
                           'route="campaigns", methods=["GET"]', 1),
            SOURCE.replace('queue_name="retail-campaign-planning"',
                           'queue_name="foreign-queue"', 1),
            SOURCE + '\n@app.queue_trigger(arg_name="message", queue_name="retail-feature4-cpu-render", connection="RETAIL_STORAGE")\ndef unexpected_worker(message):\n    pass\n',
            SOURCE + '\napp.register_functions(other_blueprint)\n',
            SOURCE.replace('route="campaigns", methods=["POST"]',
                           'route=dynamic_route, methods=["POST"]', 1),
        ]
        for changed in changes:
            self.assertNotEqual(changed, SOURCE)
            with self.subTest(change=changes.index(changed)), self.assertRaises(ValueError):
                m.verify(changed, MANIFEST)

    def test_historical_source_manifest_is_not_live_restore_evidence(self):
        historical = "\n".join(
            "@" + expr + "\ndef " + name + "():\n    pass\n"
            for name, expr in MANIFEST["legacy_bindings"].items())
        with self.assertRaises(ValueError):
            m.verify(historical, MANIFEST)


if __name__ == "__main__":
    unittest.main()
