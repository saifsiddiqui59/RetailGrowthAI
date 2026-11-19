"""Fail closed if #249 Y1 ZIP contains a redirect-leaking original TenantStore.

This is a purely offline regression with deliberately synthetic Python
modules and synthetic HTTPS redirects. No real JWT, network, Azure, database,
customer records, GPU or privileged secrets are used.
"""
from pathlib import Path
import importlib.util
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "ops/p0249-y1-readonly-extra-get/verify_staged_y1_auth_transport.py"
WORKFLOW = ROOT / ".github/workflows/p0249-dev-y1-five-get-release-manual.yml"
spec = importlib.util.spec_from_file_location("p0249_y1_auth_transport_testee", GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

SAFE = '''from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (HTTPRedirectHandler, Request, build_opener)

class StorageUnavailable(RuntimeError):
    pass

class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_NO_REDIRECT_OPENER = build_opener(_RejectRedirects())

class TenantStore:
    def __init__(self, origin, publishable_key, transport=None):
        parsed = urlsplit(origin)
        if not (parsed.scheme == "https" and parsed.hostname
                and parsed.username is None and parsed.password is None
                and parsed.path in ("", "/") and not parsed.query
                and not parsed.fragment):
            raise ValueError("invalid source origin")
        self.origin = origin.rstrip("/")
        self.key = publishable_key
        self.transport = transport if transport is not None else _NO_REDIRECT_OPENER.open

    def _request(self, table, token, *, query=None):
        req = Request(self.origin + "/rest/v1/campaigns?select=id",
                      headers={"Authorization": "Bearer " + token,
                               "apikey": self.key})
        try:
            with self.transport(req, timeout=8) as response:
                return response.read()
        except HTTPError as exc:
            try:
                raise StorageUnavailable("request denied") from exc
            finally:
                exc.close()
'''


class StagedY1AuthTransportReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tenant_store.py").write_text(SAFE, encoding="utf-8")

    def write(self, source):
        (self.root / "tenant_store.py").write_text(source, encoding="utf-8")

    def test_strict_default_denies_all_redirect_codes_without_network(self):
        guard.verify_staged_tenant_transport(self.root)

    def test_unpatched_original_default_without_guard_refused(self):
        # Reproduces original main pre-#1018: urlopen follows 30x by default.
        vulnerable = SAFE.replace(
            "from urllib.request import (HTTPRedirectHandler, Request, build_opener)",
            "from urllib.request import (HTTPRedirectHandler, Request, build_opener, urlopen)")
        vulnerable = vulnerable.replace(
            "_NO_REDIRECT_OPENER.open\n", "urlopen\n")
        vulnerable = vulnerable.replace("class _RejectRedirects(HTTPRedirectHandler):",
                                        "class _LegacyUnusedRedirects(HTTPRedirectHandler):")
        vulnerable = vulnerable.replace("_RejectRedirects()", "_LegacyUnusedRedirects()")
        self.write(vulnerable)
        with self.assertRaisesRegex(guard.GuardError,
                                    "Y1_AUTH_REDIRECT_GUARD_NOT_PRESENT"):
            guard.verify_staged_tenant_transport(self.root)

    def test_defined_but_unused_redirect_protection_is_rejected(self):
        self.write(SAFE.replace(
            "from urllib.request import (HTTPRedirectHandler, Request, build_opener)",
            "from urllib.request import (HTTPRedirectHandler, Request, build_opener, urlopen)"
        ).replace("_NO_REDIRECT_OPENER.open\n", "urlopen\n"))
        with self.assertRaisesRegex(guard.GuardError,
                                    "Y1_AUTH_REDIRECT_GUARD_NOT_DEFAULT"):
            guard.verify_staged_tenant_transport(self.root)

    def test_redirect_handler_must_reject_cross_origin_not_just_be_named(self):
        self.write(SAFE.replace(
            "        return None\n", 
            "        return super().redirect_request(req, fp, code, msg, headers, newurl)\n",
            1))
        with self.assertRaisesRegex(guard.GuardError,
                                    "Y1_AUTH_TOKEN_WOULD_LEAVE_TRUSTED_ORIGIN"):
            guard.verify_staged_tenant_transport(self.root)

    def test_initial_unsafe_https_origin_must_be_rejected(self):
        self.write(SAFE.replace(
            '        if not (parsed.scheme == "https" and parsed.hostname',
            '        if not (parsed.scheme in ("https", "http") and parsed.hostname'))
        with self.assertRaisesRegex(guard.GuardError,
                                    "Y1_AUTH_SUPABASE_ORIGIN_UNSAFE"):
            guard.verify_staged_tenant_transport(self.root)

    def test_missing_and_symlinked_source_are_denied(self):
        original = self.root / "tenant_store.py"
        backup = self.root / "owned_fixture.py"
        shutil.move(original, backup)
        with self.assertRaisesRegex(guard.GuardError, "Y1_AUTH_STAGED_SOURCE_UNREADABLE"):
            guard.verify_staged_tenant_transport(self.root)
        original.symlink_to(backup)
        with self.assertRaisesRegex(guard.GuardError, "Y1_AUTH_STAGED_SOURCE_UNREADABLE"):
            guard.verify_staged_tenant_transport(self.root)

    def test_release_runs_both_real_staged_auth_guards_before_cloud_mutation(self):
        work = WORKFLOW.read_text(encoding="utf-8")
        cmd = "verify_staged_y1_auth_transport.py"
        self.assertEqual(work.count(cmd), 2)
        self.assertIn('--target "$RUNNER_TEMP/y1-five"', work)
        self.assertIn('--target "$RUNNER_TEMP/y1-two"', work)
        gate = work.index("verify_staged_y1_auth_transport.py")
        self.assertLess(work.index("--mode rollback-two"), gate)
        self.assertLess(gate, work.index("python3 -m pip install"))
        self.assertLess(gate, work.index("- uses: azure/login@v3"))
        self.assertLess(gate, work.index("az functionapp deployment source config-zip"))
        self.assertIn("environment: dev", work)
        self.assertIn("cancel-in-progress: false", work)


if __name__ == "__main__":
    unittest.main()
