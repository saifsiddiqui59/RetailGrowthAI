"""Prevent native F4 ZIP staging without a real sealed offline index proof."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/".github/workflows/retail-dev-feature4-cpu-zip-once.yml"
SCRIPT=ROOT/"scripts/deploy/probe_feature4_cpu_native_index.py"


class CpuZipIndexProbeTests(unittest.TestCase):
    def test_package_validation_before_isolated_execution(self):
        w=WORKFLOW.read_text()
        s=SCRIPT.read_text()
        self.assertIn("verify_feature4_cpu_release.py",w)
        self.assertIn("probe_feature4_cpu_native_index.py",w)
        self.assertLess(w.index("verify_feature4_cpu_release.py"),
                        w.index("probe_feature4_cpu_native_index.py"))
        self.assertLess(w.index("probe_feature4_cpu_native_index.py"),
                        w.index("uses: Azure/functions-action@"))
        for value in (
            "verify_release(path)",
            'with ZipFile(path, "r")',
            "archive.extractall(root)",
            '"-S", "-c", _program(enabled)',
            '"RETAIL_FEATURE4_CPU_WORKER_ENABLED"',
            "subprocess.DEVNULL",
            "PYTHONNOUSERSITE",
            "feature4_cpu_dispatch_timer",
            "feature4_cpu_poison_message",
            "feature4_cpu_render_message",
        ):
            self.assertIn(value,s)
        self.assertNotIn("az functionapp config appsettings set",w)
        self.assertNotIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED: 'true'",w)
        self.assertNotIn("urllib.request",s)
        self.assertNotIn("requests.",s)

    def test_expected_off_and_on_name_sets_do_not_alias(self):
        spec=importlib.util.spec_from_file_location("rgai_cpu_probe", SCRIPT)
        # The script imports a sibling verifier; include scripts/deploy only for
        # this isolated offline test, no Azure/API connection.
        import sys
        root=str(SCRIPT.parent)
        sys.path.insert(0, root)
        try:
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertIn("[]", module._program(False))
            self.assertIn("feature4_cpu_dispatch_timer", module._program(True))
            self.assertNotIn("feature4_cpu_dispatch_timer", module._program(False))
        finally:
            sys.path.remove(root)

if __name__=="__main__":
    unittest.main()
