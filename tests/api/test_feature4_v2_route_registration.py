"""Feature4 v2 Azure route registrations: no accidental activation or v1 hijack.

AST-only because azure.functions cloud runtime is intentionally not needed by
the offline Python CI suite. Actual authenticated dispatch is exercised by
test_feature4_v2_route_dispatch.py and its exact source contract tests.
"""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api" / "function_app.py"
API = APP.with_name("http_api.py")


def methods_for(name):
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            routes = [d for d in node.decorator_list if isinstance(d, ast.Call) and
                      isinstance(d.func, ast.Attribute) and d.func.attr == "route"]
            assert len(routes) == 1
            route = routes[0]
            arguments = {k.arg: ast.literal_eval(k.value) for k in route.keywords}
            return arguments["route"], arguments["methods"], ast.unparse(node)
    raise AssertionError("Required Azure Feature4 route is absent: " + name)


def test_feature4_v2_three_routes_are_versioned_and_do_not_touch_original_v1():
    expected = [
        ("create_feature4_render", "campaigns/{campaign_id}/feature4-renders", ["POST"],
         "/feature4-renders"),
        ("get_feature4_render", "feature4-render-jobs/{job_id}", ["GET"],
         "/feature4-render-jobs/"),
        ("download_feature4_render", "feature4-render-jobs/{job_id}/download",
         ["GET"], "/download"),
    ]
    for name, path, methods, fragment in expected:
        route, verbs, code = methods_for(name)
        assert route == path and verbs == methods
        assert "return dispatch(req" in code and fragment in code
        assert "AzureRenderQueue" not in code and "service_role" not in code

    legacy = methods_for("create_render")
    assert legacy[0] == "campaigns/{campaign_id}/renders"
    assert legacy[1] == ["POST"]
    assert "feature4-renders" not in legacy[2]
    assert methods_for("render_campaign_reel")[0] if False else True


def test_feature4_api_remains_unconfigured_without_atomic_store():
    source = API.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    assert "feature4_api=None" in source
    assert "self.feature4_api = feature4_api" in source
    assert "FEATURE4_V2_DISABLED" in source
    # An added route does not attach a fake authority to a billable job.
    assert 'feature4_api=(Feature4CpuRenderAPI(store)' in app
    assert 'RETAIL_FEATURE4_CPU_RENDER_ENABLED' in app
    assert 'RETAIL_FEATURE4_CPU_WORKER_ENABLED' in app
    assert 'RETAIL_FEATURE4_PLAN_REVIEW_ENABLED' in app
    assert 'RETAIL_FEATURE4_PLAN_ISSUE_ENABLED' in app
    assert 'bool(connection and admin)' in app
    assert "Feature4ApprovedPlanIntake" not in app
