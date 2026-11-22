"""#249: Flex cannot be stopped based on five GET routes or mocked receipts."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ops/p0249-y1-cutover/retirement_gate.py"
spec = importlib.util.spec_from_file_location("p0249_y1_stop_gate", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def observation():
    return {
        "scope": {
            "resource_group": m.RG, "y1_app": m.Y1, "flex_app": m.FLEX,
            "supabase_origin": m.SUPABASE, "frontend_origin": m.FRONTEND,
        },
        "y1": {
            "host": m.Y1_ORIGIN, "state": "Running",
            "app_setting_names": sorted(m.CONNECTIONS),
            "same_retailgrowth_dev_connections_as_flex": True,
            "cors":{"allowedOrigins":[m.FRONTEND],"supportCredentials":False},
            "indexed_functions": sorted(
                m.ALL_HTTP_FUNCTIONS | m.QUEUE_FUNCTIONS | m.TIMER_FUNCTIONS),
            "unauthenticated_protected_endpoints_denied": True,
            "customer_traffic_origin": m.Y1_ORIGIN,
            "background_workers_enabled": True, "queue_backlog_reconciled": True,
        },
        "flex": {
            "host": m.FLEX_ORIGIN, "receiving_customer_traffic": False,
            "background_workers_enabled": False,
        },
        "frontend": {"served_api_origin": m.Y1_ORIGIN},
        "render_worker": {
            "hosting_mode": "isolated_on_demand_cpu_worker",
            "max_execution_seconds": 1200,
            "same_approved_shop_queue_and_lease": True,
            "private_media_and_ffmpeg_verified": True,
        },
        "protected_evidence": {name: True for name in m.PROOF},
        "verified_by_protected_release_workflow": True,
    }


class Y1NoPrematureFlexStop(unittest.TestCase):
    def test_actual_five_get_package_cannot_retire_flex(self):
        state = observation()
        state["y1"]["indexed_functions"] = [
            "p0249_health", "campaign_read", "render_job_read",
            "poster_job_read", "poster_draft_read",
        ]
        denied = m.evaluate(state)
        self.assertIn("original_core_http_routes", denied)
        self.assertIn("planning_render_poster_poison_workers", denied)
        self.assertIn("outbox_recovery_email_trend_timers", denied)

    def test_missing_optional_http_or_unknown_function_blocks_retirement(self):
        state = observation()
        self.assertEqual(len(m.ALL_HTTP_FUNCTIONS), 38)
        self.assertEqual(len(m.EXPECTED_FULL_Y1_INDEX), 46)
        self.assertEqual(m.evaluate(state), ())
        state["y1"]["indexed_functions"].remove("feature3_designs")
        self.assertIn("all_original_http_routes", m.evaluate(state))
        state = observation()
        state["y1"]["indexed_functions"].append("unreviewed_function")
        self.assertIn("unreviewed_or_duplicate_y1_function_index",
                      m.evaluate(state))
        state = observation()
        state["y1"]["indexed_functions"].append("create_campaign")
        self.assertIn("unreviewed_or_duplicate_y1_function_index",
                      m.evaluate(state))

    def test_no_data_also_blocks_retirement(self):
        self.assertIn("exact_dev_scope", m.evaluate({}))
        self.assertEqual(m.evaluate(None), ("untrusted_snapshot",))

    def test_foreign_or_modified_app_never_accepted(self):
        state = observation()
        state["scope"]["y1_app"] = "other-functions-app"
        self.assertIn("exact_dev_scope", m.evaluate(state))

    def test_missing_supabase_and_storage_connection_blocks(self):
        state = observation()
        state["y1"]["app_setting_names"].remove("RETAIL_STORAGE")
        self.assertIn("server_side_y1_supabase_storage_connections", m.evaluate(state))
        state = observation()
        state["y1"]["same_retailgrowth_dev_connections_as_flex"] = False
        self.assertIn("protected_original_connection_value_comparison",
                      m.evaluate(state))

    def test_classic_y1_must_never_index_original_780s_video_queue_worker(self):
        state=observation()
        state["y1"]["indexed_functions"].append("render_campaign_reel")
        self.assertIn("classic_y1_must_not_index_780s_render_consumer",
                      m.evaluate(state))

    def test_unmodified_classic_y1_cannot_claim_780_second_render_worker(self):
        self.assertEqual(m.CLASSIC_CONSUMPTION_MAX_SECONDS, 600)
        self.assertEqual(m.ORIGINAL_RENDER_HARD_CAP_SECONDS, 780)
        state = observation()
        state["render_worker"] = {
            "hosting_mode": "classic_y1_consumption",
            "max_execution_seconds": 600,
            "same_approved_shop_queue_and_lease": True,
            "private_media_and_ffmpeg_verified": False,
        }
        self.assertIn("long_render_worker_incompatible_with_classic_y1_600s_limit",
                      m.evaluate(state))
        state = observation()
        state["render_worker"]["max_execution_seconds"] = 540
        self.assertIn("long_render_worker_incompatible_with_classic_y1_600s_limit",
                      m.evaluate(state))
        state = observation()
        state["render_worker"]["private_media_and_ffmpeg_verified"] = False
        self.assertIn("long_render_worker_incompatible_with_classic_y1_600s_limit",
                      m.evaluate(state))

    def test_all_38_original_http_routes_required_not_just_core(self):
        import importlib.util
        converter = ROOT / "ops/p0249-y1-cutover/prepare_http_only.py"
        spec = importlib.util.spec_from_file_location("p0249_full_y1_parity", converter)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(m.ALL_HTTP_FUNCTIONS, module.HTTP | {"p0249_health"})
        self.assertEqual(len(m.ALL_HTTP_FUNCTIONS), 38)
        self.assertEqual(len(m.EXPECTED_FULL_Y1_INDEX), 46)
        state = observation()
        state["y1"]["indexed_functions"].remove("create_private_voicestudio_job")
        self.assertIn("all_original_http_routes", m.evaluate(state))
        state = observation()
        state["y1"]["indexed_functions"].append("unknown_experimental_route")
        self.assertIn("unreviewed_or_duplicate_y1_function_index", m.evaluate(state))
        state = observation()
        state["y1"]["indexed_functions"].append("read_campaign")
        self.assertIn("unreviewed_or_duplicate_y1_function_index", m.evaluate(state))

    def test_public_api_exact_development_cors_required(self):
        state=observation()
        state["y1"]["cors"]["allowedOrigins"]=["*"]
        self.assertIn("y1_exact_dev_frontend_cors",m.evaluate(state))
        state=observation()
        state["y1"]["cors"]["allowedOrigins"]=["https://foreign.example"]
        self.assertIn("y1_exact_dev_frontend_cors",m.evaluate(state))
        state=observation()
        state["y1"]["cors"]["supportCredentials"]=True
        self.assertIn("y1_exact_dev_frontend_cors",m.evaluate(state))

    def test_untransferred_customer_traffic_blocks(self):
        state = observation()
        state["frontend"]["served_api_origin"] = m.FLEX_ORIGIN
        state["flex"]["receiving_customer_traffic"] = True
        self.assertIn("frontend_live_cutover", m.evaluate(state))
        self.assertIn("flex_customer_traffic_still_possible", m.evaluate(state))

    def test_no_dual_workers_or_unknown_queue_inflight(self):
        state = observation()
        state["flex"]["background_workers_enabled"] = True
        state["y1"]["queue_backlog_reconciled"] = False
        self.assertIn("flex_workers_still_active", m.evaluate(state))
        self.assertIn("y1_queue_drain_or_unknown_work", m.evaluate(state))

    def test_cannot_claim_completion_without_hosted_evidence(self):
        state = observation()
        state["protected_evidence"]["quota_billing_idempotency"] = False
        self.assertIn("independent_hosted_e2e_and_rollback_receipts",
                      m.evaluate(state))
        state = observation()
        state["verified_by_protected_release_workflow"] = False
        self.assertIn("protected_release_origin_unverified", m.evaluate(state))

    def test_fully_asserted_json_never_executes_stop(self):
        self.assertEqual(m.evaluate(observation()), ())
        text = SOURCE.read_text()
        self.assertIn("BLOCKED_PENDING_PROTECTED_AZURE_ACCEPTANCE", text)
        self.assertNotIn("az functionapp stop", text)
        self.assertNotIn("az functionapp delete", text)
        self.assertNotIn("az group delete", text)
        self.assertNotIn("github.issues.update", text)


if __name__ == "__main__":
    unittest.main()
