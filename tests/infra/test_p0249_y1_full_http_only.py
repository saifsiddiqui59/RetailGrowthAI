"""#249 Y1 parity: original HTTP routes only, with ZERO duplicate workers.

These are source/ZIP preparation checks, not a hosted DEV acceptance or a
license to stop the original Flex host.
"""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ops/p0249-y1-cutover/prepare_http_only.py"
MODULE = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location("p0249_full_y1_http", SOURCE))
MODULE.__spec__.loader.exec_module(MODULE)


def nodes(source):
    tree = ast.parse(source)
    return {node.name: ast.dump(node, include_attributes=False)
            for node in tree.body if isinstance(node, ast.FunctionDef)}


class Y1FullHttpOnlySourceTests(unittest.TestCase):
    def test_all_original_http_handlers_preserved_and_no_background_consumers(self):
        original = MODULE.ORIGINAL.read_bytes()
        prepared = MODULE.strip_only_background_triggers(original)
        before, _ = MODULE.registrations(original)
        after, _ = MODULE.registrations(prepared)
        self.assertEqual(set(before), MODULE.HTTP | MODULE.WORKERS)
        self.assertEqual(set(after), MODULE.HTTP | {"p0249_health"})
        self.assertEqual(set(after.values()), {"route"})
        self.assertEqual(len(MODULE.WORKERS), 9)
        self.assertGreaterEqual(len(MODULE.HTTP), 30)
        self.assertIn(b'json.dumps({"status":"ok","canary":"classic-y1-v1-p0249"})', prepared)
        self.assertNotIn(b"@app.queue_trigger", prepared)
        self.assertNotIn(b"@app.timer_trigger", prepared)
        for name in MODULE.HTTP:
            self.assertEqual(nodes(original)[name], nodes(prepared)[name], name)
        for name in ("build_api", "dispatch", "build_feature2_api",
                     "dispatch_feature2", "build_feature2_voicestudio_api"):
            self.assertEqual(nodes(original)[name], nodes(prepared)[name], name)

    def test_original_auth_queue_outbox_billing_methods_remain_original(self):
        source = MODULE.strip_only_background_triggers(MODULE.ORIGINAL.read_bytes())
        for sentinel in (b"cached_supabase_verifier", b"TenantStore",
                         b"AdminStore", b"AzurePlanningQueue",
                         b"AzureRenderQueue", b"durable_outbox",
                         b"PosterRenderAPI", b"HTTPAPI", b"feature3_api"):
            self.assertIn(sentinel, source)
        for name in MODULE.CORE_HTTP:
            self.assertIn(name, MODULE.HTTP)

    def test_unknown_worker_added_to_original_requires_new_review(self):
        source = MODULE.ORIGINAL.read_bytes()
        self.assertIn(b"@app.queue_trigger", source)
        tampered = source + b"""
@app.queue_trigger(arg_name="message", queue_name="unreviewed",
                   connection="RETAIL_STORAGE")
def unreviewed_worker(message):
    return None
"""
        with self.assertRaisesRegex(ValueError, "registrations drifted"):
            MODULE.strip_only_background_triggers(tampered)

    def test_worker_changed_into_http_must_fail_closed(self):
        source = MODULE.ORIGINAL.read_bytes()
        tampered = source.replace(b'@app.queue_trigger(', b'@app.route(', 1)
        self.assertNotEqual(source, tampered)
        with self.assertRaisesRegex(ValueError, "registrations drifted"):
            MODULE.strip_only_background_triggers(tampered)

    def test_removed_required_worker_refuses_conversion(self):
        source = MODULE.ORIGINAL.read_bytes()
        tampered = source.replace(b"def planning_poison(", b"def renamed_poison(", 1)
        self.assertNotEqual(source, tampered)
        with self.assertRaisesRegex(ValueError, "registrations drifted"):
            MODULE.strip_only_background_triggers(tampered)

    def test_unreviewed_http_route_requires_new_review(self):
        source = MODULE.ORIGINAL.read_bytes()
        tampered = source + b"""
@app.route(route="public-unreviewed-secret",methods=["GET"])
def unreviewed_public_endpoint(req):
    return None
"""
        with self.assertRaisesRegex(ValueError, "registrations drifted"):
            MODULE.strip_only_background_triggers(tampered)

    def test_no_cloud_shutdown_or_config_write_in_package_script(self):
        text = SOURCE.read_text()
        self.assertNotIn("az functionapp stop", text)
        self.assertNotIn("az functionapp delete", text)
        self.assertNotIn("AzureWebJobs.", text)
        self.assertNotIn("requests.post", text)
        self.assertNotIn("subprocess.run(", text)
        self.assertIn("original_packager.verify_zip(source)", text)
        self.assertIn("original_packager.verify_zip(destination)", text)
        self.assertIn("Source ZIP does not match the checked-out original", text)


if __name__ == "__main__":
    unittest.main()
