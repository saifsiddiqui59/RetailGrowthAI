"""Gateway availability must be checked before disposable DEV user creation."""
import importlib.util
import io
from pathlib import Path
from urllib.error import HTTPError

import pytest

SOURCE=Path(__file__).with_name("retail_dev_canary_once.py")
SPEC=importlib.util.spec_from_file_location("retail_dev_canary_once",SOURCE)
canary=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)


def make_transport(statuses):
    seen=[]
    remaining=iter(statuses)
    def transport(req,timeout=0):
        seen.append((req.get_method(),req.full_url,timeout,dict(req.header_items())))
        status,has_handler=next(remaining)
        headers={"X-Request-ID":"opaque"} if has_handler else {}
        raise HTTPError(req.full_url,status,"safe",headers,io.BytesIO(b'{}'))
    return transport,seen


def test_four_authenticated_boundaries_return_fast_401_without_real_jwt():
    send,seen=make_transport([(401,True)]*4)
    assert canary.preflight_dev_http_auth_routes(transport=send,clock=lambda:1) is None
    assert len(seen)==4
    assert [m for m,*_ in seen]==["GET","GET","GET","POST"]
    assert all(timeout==12 for _,_,timeout,_ in seen)
    assert all("Authorization" not in headers for _,_,_,headers in seen)
    assert all(url.startswith(canary.API+"/api/") for _,url,_,_ in seen)
    assert all("11111111-1111-4111-8111-111111111111" in url
               for _,url,_,_ in seen[:3])


@pytest.mark.parametrize("code,header",[
    (503,False),(502,False),(504,False),(200,False),
    (401,False),(404,True),(500,True)
])
def test_gateway_errors_and_missing_function_marker_never_authorize_accounts(code,header):
    send,seen=make_transport([(code,header)]+[(401,True)]*3)
    with pytest.raises(RuntimeError,match="before test account creation"):
        canary.preflight_dev_http_auth_routes(transport=send,clock=lambda:1)
    assert len(seen)==1


def test_preflight_socket_timeout_fails_before_creating_any_accounts():
    def timeout(_req,timeout=0):
        assert timeout==12
        raise TimeoutError("non-logged private network error")
    with pytest.raises(RuntimeError,match="before test account creation"):
        canary.preflight_dev_http_auth_routes(transport=timeout,clock=lambda:1)


def test_preflight_latency_over_budget_fails_closed():
    send,seen=make_transport([(401,True)]*4)
    times=iter([0.0,12.5])
    with pytest.raises(RuntimeError,match="before test account creation"):
        canary.preflight_dev_http_auth_routes(transport=send,clock=lambda:next(times))
    assert len(seen)==1


def test_real_main_runs_gateway_probe_before_deleting_or_creating_test_users():
    src=SOURCE.read_text()
    main=src.split("\ndef main():\n",1)[1]
    # Auth admin POST lives in the stage helper; main still performs the
    # real HTTP preflight BEFORE calling the helper and creating any user.
    assert main.index("preflight_dev_http_auth_routes(include_prompt=prompt_only)") < main.index(
        "account_password_a = stage_two_root_gated_accounts(")
    assert '"/auth/v1/admin/users"' in src
    assert main.index("wait_for_both_root_approvals(accounts)") < main.index(
        'call(SUPABASE+"/rest/v1/shops",')
    assert "CANARY_DEV_GATEWAY_AUTH_PREFLIGHT_PASSED=true" in src
