"""F2-19/20 real source HTTP route dispatch (isolated Azure host harness).

Protected function_app source is loaded as the ACTUAL four AST functions,
without loading unrelated Azure queue/paid-model APIs. Real Azure deployment,
JWT/database provider and protected package activation are NOT simulated as
successful here. The gateway's real tenant/backend integration is separately
tested in test_feature2_private_voice_store_gateway.py.
"""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE=Path(__file__).resolve().parents[2]/(
    "azure-functions/campaign-api/function_app.py")
ROUTES=(
    "build_feature2_private_voice",
    "dispatch_feature2_private_voice",
    "feature2_private_voice_job_status",
    "feature2_private_original_wav",
)
SHOP="11111111-1111-4111-8111-111111111111"
CAMPAIGN="22222222-2222-4222-8222-222222222222"
REQUEST="55555555-5555-4555-8555-555555555555"
ASSET="44444444-4444-4444-8444-444444444444"
SHA="a"*64

class Response:
    def __init__(self,body,status_code,mimetype,headers):
        self.body=body
        self.status_code=status_code
        self.mimetype=mimetype
        self.headers=headers

class Diagnostics:
    def __init__(self,method,path):
        self.method=method
        self.path=path
    def complete(self,code,payload):
        assert self.method=="GET"
        assert "Authorization" not in self.path
        # No private audio bytes should ever be passed to the diagnostics.
        assert type(payload) is dict
        assert not any(type(x) is bytes for x in payload.values())
        return {"X-RGAI-Review":"synthetic-offline-test"}

def request(*,authorization="Bearer signed",kind="status"):
    return SimpleNamespace(
        route_params={
            "shop_id":SHOP,"campaign_id":CAMPAIGN,
            "request_key":REQUEST,
            "audio_asset_id":ASSET,"original_audio_sha256":SHA,
        },
        headers={"Authorization":authorization},
    )

def source_funcs():
    syntax=ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes=[]
    for node in syntax.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and (
            node.name in ROUTES
        ):
            node.decorator_list=[]  # fake host has no actual Azure decorators
            nodes.append(node)
    assert len(nodes)==4
    return ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))

def harness(monkeypatch,handler=None,enabled=False):
    monkeypatch.setenv("RETAIL_FEATURE2_PRIVATE_VOICE_READ",
                       "true" if enabled else "false")
    ns={"os":os,"json":json,"RequestDiagnostics":Diagnostics,
        "func":SimpleNamespace(HttpRequest=object,HttpResponse=Response)}
    exec(compile(source_funcs(),str(SOURCE),"exec"),ns)
    if handler is not None:
        ns["build_feature2_private_voice"]=lambda:handler
    return ns

def test_f2_19_20_missing_reviewed_package_is_503_without_credentials(monkeypatch):
    api=harness(monkeypatch)
    assert api["build_feature2_private_voice"]() is None
    for kind in ("status","original_wav"):
        response=api["dispatch_feature2_private_voice"](
            request(authorization="Bearer wrong"),kind=kind)
        assert response.status_code==503
        assert response.mimetype=="application/json"
        assert "DISABLED" in json.loads(response.body)["error"]
        assert "signed" not in response.body

def test_f2_19_valid_source_status_dispatches_get_only_and_sanitizes(monkeypatch):
    records=[]
    class Gateway:
        def read_status(self,*args):
            records.append(args)
            return 200,{"schema":"retailgrowth.feature2-private-voice-job-status.v1",
                        "status":"RUNNING","private":True,"can_publish":False}
        def read_original_wav(self,*args):
            raise AssertionError("A status request must not fetch audio")
    api=harness(monkeypatch,Gateway(),enabled=True)
    response=api["feature2_private_voice_job_status"](request())
    assert response.status_code==200
    assert response.mimetype=="application/json"
    assert json.loads(response.body)["status"]=="RUNNING"
    assert records==[(SHOP,CAMPAIGN,REQUEST,"Bearer signed")]
    assert response.headers["X-RGAI-Review"]=="synthetic-offline-test"

def test_f2_20_wav_is_binary_no_store_and_never_serialized(monkeypatch):
    class Gateway:
        def read_status(self,*args):
            raise AssertionError("Unexpected job-status request")
        def read_original_wav(self,*args):
            assert args==(SHOP,CAMPAIGN,ASSET,SHA,"Bearer signed")
            return 200,{"body":b"RIFF"+b"\0"*300,
                        "headers":{"Content-Type":"audio/wav",
                            "Cache-Control":"private, no-store",
                            "Pragma":"no-cache",
                            "X-Content-Type-Options":"nosniff"}}
    api=harness(monkeypatch,Gateway(),enabled=True)
    response=api["feature2_private_original_wav"](request(kind="wav"))
    assert response.status_code==200
    assert response.mimetype=="audio/wav"
    assert response.body==b"RIFF"+b"\0"*300
    assert response.headers["Cache-Control"]=="private, no-store"
    assert response.headers["X-Content-Type-Options"]=="nosniff"
    assert response.headers["X-RGAI-Review"]=="synthetic-offline-test"

@pytest.mark.parametrize("broken",[
    {"body":b"RIFF","headers":{"Cache-Control":"private, no-store",
                              "Content-Type":"audio/wav"}},
    {"body":b"RIFF"+b"\0"*200,"headers":{"Cache-Control":"public",
                                "Content-Type":"audio/wav"}},
    {"body":b"RIFF"+b"\0"*200,"headers":{"Cache-Control":"private, no-store",
                                "Content-Type":"text/html"}},
    {"body":"some-fake-public-URL","headers":{"Cache-Control":"private, no-store",
                                      "Content-Type":"audio/wav"}},
])
def test_f2_20_invalid_gateway_binary_never_becomes_a_download(monkeypatch,broken):
    class Gateway:
        def read_original_wav(self,*_):
            return 200,broken
    api=harness(monkeypatch,Gateway(),enabled=True)
    response=api["feature2_private_original_wav"](request())
    assert response.status_code==503
    assert response.mimetype=="application/json"
    assert "body" not in json.loads(response.body)
    assert "signed" not in response.body

def test_f2_19_errors_never_reflect_backend_exceptions_or_jwt(monkeypatch):
    class Gateway:
        def read_status(self,*_):
            raise RuntimeError("Bearer signed customer secret")
    api=harness(monkeypatch,Gateway(),enabled=True)
    response=api["feature2_private_voice_job_status"](request())
    assert response.status_code==503
    assert response.mimetype=="application/json"
    assert "Bearer signed" not in response.body
    assert json.loads(response.body)=={
        "error":"FEATURE2_PRIVATE_VOICE_UNAVAILABLE"}

def test_f2_19_20_routes_are_distinct_get_only_and_have_opt_in_guard():
    syntax=ast.parse(SOURCE.read_text())
    funcs={n.name:n for n in syntax.body if isinstance(n,ast.FunctionDef)}
    for name in ("feature2_private_voice_job_status",
                 "feature2_private_original_wav"):
        node=funcs[name]
        assert len(node.decorator_list)==1
        decorator=node.decorator_list[0]
        assert isinstance(decorator,ast.Call)
        assert any(kw.arg=="methods" and
                   isinstance(kw.value,ast.List) and
                   len(kw.value.elts)==1 and
                   kw.value.elts[0].value=="GET"
                   for kw in decorator.keywords)
    body=ast.get_source_segment(SOURCE.read_text(),
                                funcs["build_feature2_private_voice"])
    assert '!= "true"' in body
    assert "RETAIL_SUPABASE_PUBLISHABLE_KEY" in body
    assert "RETAIL_SUPABASE_SERVICE_ROLE_KEY" not in body
    assert "read_private_local_voice_job_status" in body
    assert "read_registered_private_original_wav" in body
