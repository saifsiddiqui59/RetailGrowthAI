"""Offline deny-write checks for hosted Y1 two-route idle read-only workflow."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/".github/workflows/p0249-dev-y1-two-route-idle-readonly-once.yml"


class Y1TwoRouteIdleReadOnlyTests(unittest.TestCase):
    def test_only_isolated_dev_and_owner_confirmed_dispatch(self):
        w=WORKFLOW.read_text()
        for token in ("environment: dev","id-token: write","refs/heads/main",
                      "YES-Y1-READONLY-2ROUTE",
                      "rgai-dev-y1-p0249-d4e5ddbd",
                      "p0249_y1_canary_guard.py verify"):
            with self.subTest(token=token):
                self.assertIn(token,w)

    def test_no_azure_writes_or_real_user_token_bypass(self):
        w=WORKFLOW.read_text()
        for forbidden in ("az deployment group create","az functionapp create",
                          "az functionapp deployment source","az functionapp restart",
                          "az functionapp config appsettings set",
                          "az functionapp config appsettings delete",
                          "az functionapp scale config always-ready",
                          "az resource delete","az storage queue",
                          "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
                          "VITE_API_URL","--authorization"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,w)

    def test_two_real_indexed_get_routes_and_original_negative_auth(self):
        w=WORKFLOW.read_text()
        self.assertIn('{"p0249_health","campaign_read"}',w)
        self.assertIn('status==401 and marker',w)
        self.assertIn('g.probe()',w)
        self.assertIn('DENIAL_12_12=PASS',w)

    def test_after_idle_second_window_not_just_warm_burst(self):
        w=WORKFLOW.read_text()
        self.assertIn('("immediate","after_240s_idle")',w)
        self.assertIn('time.sleep(240)',w)
        self.assertIn('P0249_Y1_START_IDLE_SECONDS=240',w)
        self.assertIn('HEALTH_20_20_EACH=PASS',w)
        self.assertLess(w.index('p0249_y1_canary_guard.py verify'),
                        w.index('python3 -u - <<'))


if __name__=="__main__":
    unittest.main()
