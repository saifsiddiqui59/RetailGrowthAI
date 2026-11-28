"""Offline proof of served Vite graph cutover/rollback verifier."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("swa_origin", ROOT / "scripts/deploy/verify_p0249_swa_origin.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class ServedOriginProof(unittest.TestCase):
    def fixtures(self, origin=tool.Y1):
        html = '<div id="root"></div><script type="module" src="/assets/index-abc123.js"></script>'
        graph = {route: html for route in tool.ROUTES}
        graph.update({
            "/assets/index-abc123.js": 'import("./Campaign-abcd.js");import("/assets/Video-efgh.js");',
            "/assets/Campaign-abcd.js": 'const api="' + origin + '";import("./Shared-ijkl.js");',
            "/assets/Video-efgh.js": 'import("./Shared-ijkl.js");',
            "/assets/Shared-ijkl.js": 'import("./Campaign-abcd.js");',
        })
        return graph

    def test_y1_and_rollback_actual_reachable_graph(self):
        for origin in (tool.Y1, tool.FLEX):
            fixture = self.fixtures(origin)
            self.assertEqual(tool.verify(origin, fixture.__getitem__), 4)

    def test_old_origin_in_lazy_chunk_or_foreign_origin_fails(self):
        for origin in (tool.FLEX, "https://other-app.azurewebsites.net",
                       tool.Y1.replace("https://", "http://")):
            graph = self.fixtures()
            graph["/assets/Video-efgh.js"] += 'const second="' + origin + '";'
            with self.subTest(origin=origin), self.assertRaisesRegex(RuntimeError, "ABSENT_MIXED_OR_FOREIGN"):
                tool.verify(tool.Y1, graph.__getitem__)

    def test_missing_expected_origin_fails(self):
        graph = self.fixtures()
        graph["/assets/Campaign-abcd.js"] = 'const api="";'
        with self.assertRaisesRegex(RuntimeError, "ABSENT_MIXED_OR_FOREIGN"):
            tool.verify(tool.Y1, graph.__getitem__)

    def test_stale_route_or_external_script_fails(self):
        graph = self.fixtures()
        graph[tool.ROUTES[0]] = graph[tool.ROUTES[0]].replace("index-abc123.js", "index-old.js")
        with self.assertRaisesRegex(RuntimeError, "INCONSISTENT_ROUTE_BUILD"):
            tool.verify(tool.Y1, graph.__getitem__)
        graph = self.fixtures()
        graph[tool.ROUTES[0]] += '<script src="https://external.invalid/a.js"></script>'
        with self.assertRaisesRegex(RuntimeError, "ENTRY_INVALID"):
            tool.verify(tool.Y1, graph.__getitem__)

    def test_missing_chunk_and_unapproved_expected_origin_fail(self):
        graph = self.fixtures()
        del graph["/assets/Shared-ijkl.js"]
        with self.assertRaises(KeyError):
            tool.verify(tool.Y1, graph.__getitem__)
        with self.assertRaises(ValueError):
            tool.verify("https://foreign.invalid", graph.__getitem__)


if __name__ == "__main__":
    unittest.main()
