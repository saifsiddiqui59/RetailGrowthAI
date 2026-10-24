"""Regression: Azure Functions HTTP startup must not load heavy media engines.

AST-only assertions avoid importing Azure SDK or running cloud/FFmpeg in CI.
Worker triggers still use the exact original worker code when invoked.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "azure-functions/campaign-api/function_app.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))

HEAVY = {"poster_worker", "private_poster_media", "render_worker", "private_media"}


def _module_imports():
    return {node.module for node in TREE.body if isinstance(node, ast.ImportFrom)}


def _function(name):
    found=[node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name==name]
    assert len(found)==1
    return found[0]


def _local_imports(name):
    return {node.module for node in ast.walk(_function(name))
            if isinstance(node, ast.ImportFrom)}


def test_http_module_import_does_not_load_pillow_or_ffmpeg_workers():
    assert not (HEAVY & _module_imports()), _module_imports()


def test_queue_triggers_still_import_the_same_working_engines_at_runtime():
    assert {"render_worker","private_media"} <= _local_imports("render_campaign_reel")
    assert {"poster_worker","private_poster_media"} <= _local_imports("render_campaign_poster")
    assert "poster_worker" in _local_imports("dispatch_pending_posters")


def test_disabled_poster_queue_fails_before_loading_worker_engine():
    node=_function("render_campaign_poster")
    assert isinstance(node.body[0],ast.If)
    assert any(isinstance(x,ast.Raise) for x in ast.walk(node.body[0]))
    assert isinstance(node.body[1],ast.ImportFrom)
    assert node.body[1].module=="poster_worker"


def test_disabled_poster_dispatch_returns_before_importing_worker_engine():
    node=_function("dispatch_pending_posters")
    guard=[index for index,item in enumerate(node.body) if isinstance(item,ast.If)
           and any(isinstance(x,ast.Return) for x in ast.walk(item))]
    local_import=[index for index,item in enumerate(node.body) if isinstance(item,ast.ImportFrom)
                  and item.module=="poster_worker"]
    assert guard and local_import and guard[0]<local_import[0]


def test_public_http_adapter_still_declared_and_jwt_path_not_removed():
    names={node.name for node in TREE.body if isinstance(node,ast.FunctionDef)}
    assert {"build_api","dispatch","create_campaign","read_campaign",
            "request_poster_render","select_poster_banner",
            "render_campaign_reel","render_campaign_poster","dispatch_pending_posters"} <= names
    assert "SupabaseJWTVerifier" in SOURCE.read_text(encoding="utf-8")
