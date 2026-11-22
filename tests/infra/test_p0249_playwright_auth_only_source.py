"""Fail-closed static checks for protected temporary-user browser login mode."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / 'frontend/e2e/dev-canary-auth-login-only.mjs'
PY = ROOT / 'tests/e2e/p0249_dev_playwright_login_only_once.py'
WORKFLOW = ROOT / '.github/workflows/retail-dev-test-accounts-canary-once.yml'


class ProtectedLoginOnlySourceTests(unittest.TestCase):
    def test_two_isolated_real_chromium_logins_and_logouts(self):
        code = JS.read_text()
        self.assertEqual(subprocess.run(['node', '--check', str(JS)], capture_output=True).returncode, 0)
        for fragment in ('chromium.launch', 'browser.newContext', "'/account'",
                         "getByLabel('Email'", "getByLabel('Password'", "name: 'Sign in'",
                         "name: 'Sign out'", 'P0249_PLAYWRIGHT_TWO_DISPOSABLE_AUTH_LOGINS=PASS'):
            self.assertIn(fragment, code)
        self.assertNotIn('service_role', code)
        self.assertNotIn('page.screenshot(', code)

    def test_admin_user_cleanup_is_exact_and_always_runs(self):
        code = PY.read_text()
        for fragment in ('GITHUB_ACTIONS', 'GITHUB_REPOSITORY', 'refs/heads/main',
                         'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY', 'helper.admin_headers',
                         'helper.owner_only_cleanup', "finally:", 'capture_output=True',
                         'P0249_PLAYWRIGHT_AUTH_ONLY=PASS_NOT_SHOP_RLS_OR_Y1_WRITE'):
            self.assertIn(fragment, code)
        self.assertNotIn('auth.users', code)
        self.assertNotIn('CREATE ROLE', code)
        self.assertNotIn('createShop', code)

    def test_existing_workflow_retains_manual_protected_gate(self):
        code = WORKFLOW.read_text()
        self.assertIn('workflow_dispatch:', code)
        self.assertNotIn('\n  push:', code)
        self.assertIn('environment: dev', code)
        self.assertIn("github.ref == 'refs/heads/main'", code)
        self.assertIn('auth-login-only', code)
        self.assertIn('tests/e2e/p0249_dev_playwright_login_only_once.py', code)
        self.assertIn('RGAI_DEV_LOGIN_ONLY:', code)
        self.assertIn('RGAI_DEV_SERVICE_KEY:', code)


if __name__ == '__main__':
    unittest.main()
