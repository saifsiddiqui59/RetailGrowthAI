"""Issue #249 source regression: HTTP function indexing must not eagerly import workers.

These checks prove import placement, not an Azure latency or startup repair. The
existing four-job CI still exercises the real Python API and synthetic FFmpeg.
"""
import ast
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[2] /
          "azure-functions" / "campaign-api" / "function_app.py")
WORKER_ONLY = {
    "planning_worker", "recovery_runtime", "notification_store",
    "notification_worker", "poster_admin", "poster_queue",
}
EXPECTED_IMPORTS = {
    "plan_campaign": {"planning_worker"},
    "recover_stale_jobs": {"recovery_runtime"},
    "planning_poison": {"recovery_runtime"},
    "render_poison": {"recovery_runtime"},
    "dispatch_onboarding_emails": {"notification_store", "notification_worker"},
    "dispatch_pending_posters": {"poster_admin", "poster_queue"},
    "render_campaign_poster": {"poster_admin"},
}


def parsed():
    source = SOURCE.read_text(encoding="utf-8")
    compile(source, str(SOURCE), "exec")
    return ast.parse(source)


def imports(nodes):
    found = set()
    for node in nodes:
        for nested in ast.walk(node):
            if isinstance(nested, ast.ImportFrom) and nested.module:
                found.add(nested.module)
            elif isinstance(nested, ast.Import):
                found.update(alias.name for alias in nested.names)
    return found


def functions_by_name(tree):
    return {n.name: n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_worker_only_modules_not_imported_during_function_indexing():
    tree = parsed()
    # Import statements in function bodies are deliberately excluded here.
    top_level = [n for n in tree.body if not isinstance(n, (ast.FunctionDef,
                                                            ast.AsyncFunctionDef))]
    assert not (imports(top_level) & WORKER_ONLY)


def test_each_worker_import_stays_inside_its_own_trigger():
    tree = parsed()
    funcs = functions_by_name(tree)
    for handler, modules in EXPECTED_IMPORTS.items():
        assert modules.issubset(imports([funcs[handler]])), handler
    for handler in ("build_api", "dispatch", "build_feature2_api",
                    "dispatch_feature2", "_recovery_dependencies"):
        assert not (imports([funcs[handler]]) & WORKER_ONLY), handler


def test_worker_imports_are_not_reached_before_disabled_flag_guards():
    funcs = functions_by_name(parsed())
    for handler, flag in (
        ("dispatch_onboarding_emails", "RETAIL_NOTIFICATIONS_ENABLED"),
        ("dispatch_pending_posters", "RETAIL_ENABLE_POSTER_RENDERING"),
        ("render_campaign_poster", "RETAIL_ENABLE_POSTER_RENDERING"),
    ):
        nodes = funcs[handler].body
        guard = next((n for n in nodes if isinstance(n, ast.If) and
                      flag in ast.unparse(n.test)), None)
        assert guard is not None, handler
        # Disabled timers return; the poster queue must RAISE to avoid
        # acknowledging/deleting a legitimate queued event while disabled.
        denial = ast.Raise if handler == "render_campaign_poster" else ast.Return
        assert any(isinstance(n, denial) for n in guard.body), handler
        for n in nodes:
            if isinstance(n, ast.ImportFrom) and n.module in WORKER_ONLY:
                assert n.lineno > guard.end_lineno, handler


def test_auth_and_queue_routes_remain_declared_and_diagnostics_preserved():
    tree = parsed()
    funcs = functions_by_name(tree)
    assert "SupabaseJWTVerifier" in SOURCE.read_text(encoding="utf-8")
    assert "RequestDiagnostics" in SOURCE.read_text(encoding="utf-8")
    expected = {
        "plan_campaign": "queue_trigger",
        "render_campaign_reel": "queue_trigger",
        "planning_poison": "queue_trigger",
        "render_poison": "queue_trigger",
        "render_campaign_poster": "queue_trigger",
        "recover_stale_jobs": "timer_trigger",
        "dispatch_onboarding_emails": "timer_trigger",
        "dispatch_pending_posters": "timer_trigger",
    }
    for handler, expected_decorator in expected.items():
        decorators = funcs[handler].decorator_list
        assert any(isinstance(n, ast.Call) and
                   isinstance(n.func, ast.Attribute) and
                   n.func.attr == expected_decorator for n in decorators), handler
