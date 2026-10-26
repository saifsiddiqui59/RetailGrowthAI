#!/usr/bin/env python3
"""Actual two-session PostgreSQL budget race with one reserved max charge.

ONLY tests against the CI ephemeral database with explicit localhost marker.
Never runs Azure or calls Supabase hosted; no paid inference.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOP = "f2b00000-0000-4000-8000-000000000011"
ACTOR = "f2a00000-0000-4000-8000-000000000011"
MIGRATION = "supabase/migrations/20261026194000_feature2_ai_cost_ledger.sql"
BASE = ["psql", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1"]
CHILDREN = []
REQUIRED = {
    "RETAIL_DISPOSABLE_POSTGRES": "1",
    "PGHOST": "127.0.0.1", "PGPORT": "54322",
    "PGDATABASE": "postgres", "PGUSER": "postgres",
}
for key, value in REQUIRED.items():
    if os.environ.get(key) != value:
        raise SystemExit("REFUSED: Feature2 race requires flagged CI disposable PostgreSQL")
if not os.environ.get("PGPASSWORD"):
    raise SystemExit("REFUSED: missing local disposable password")


def call(sql, *, application="feature2-ai-budget-check", allowed=(0,)):
    completed = subprocess.run(BASE + ["-c", sql], cwd=ROOT,
        env=dict(os.environ, PGAPPNAME=application),
        text=True, capture_output=True, timeout=35, check=False)
    if completed.returncode not in allowed:
        raise AssertionError("Budget SQL failed: "+completed.stderr[-1300:])
    return completed


def launch(sql, app):
    child = subprocess.Popen(BASE + ["-c", sql], cwd=ROOT,
        env=dict(os.environ, PGAPPNAME=app),
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    CHILDREN.append(child)
    return child


def finish(child, label, timeout=25):
    try:
        out, err = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(label+" SQL lock timed out") from exc
    return child.returncode, out, err


def waiter_count():
    return int(call(
        "select count(*) from pg_catalog.pg_stat_activity where "
        "application_name in ('f2-budget-race-a','f2-budget-race-b') "
        "and wait_event_type='Lock'").stdout.strip().splitlines()[-1])


def check():
    source=(ROOT/MIGRATION).read_text()
    if "create function public.feature2_reserve_ai_budget(" not in source:
        raise AssertionError("Wrong canonical budget ledger migration")
    setup = subprocess.run(
        BASE+["-f","tests/security/feature2_ai_budget_concurrency_setup.sql"],
        cwd=ROOT,env=dict(os.environ, PGAPPNAME="f2-budget-race-setup"),
        text=True,capture_output=True,timeout=30,check=False)
    if setup.returncode:
        raise AssertionError(setup.stderr[-1200:])

    locker = launch(
        "begin; select shop_id from public.shop_subscriptions "
        f"where shop_id='{SHOP}' for update; select pg_sleep(14); commit;",
        "f2-budget-race-locker")
    time.sleep(0.8)
    if locker.poll() is not None:
        raise AssertionError("Subscription lock holder ended before concurrent requests")
    def req(request_id):
        return (
        "begin; set local role service_role; "
        "select set_config('request.jwt.claims',"
        f" '{{\"role\":\"service_role\",\"sub\":\"{ACTOR}\"}}',true); "
        "select 'F2_RECEIPT:' || "
        f"public.feature2_reserve_ai_budget('{SHOP}','{ACTOR}','prompt',0.003,'{request_id}')::text; "
        "commit;"
    )
    first=launch(req("f2d00000-0000-4000-8000-000000000011"),"f2-budget-race-a")
    second=launch(req("f2d00000-0000-4000-8000-000000000012"),"f2-budget-race-b")
    until=time.monotonic()+10
    while waiter_count()<2 and time.monotonic()<until:
        if first.poll() is not None or second.poll() is not None:
            raise AssertionError("Concurrent model budget waiter exited before row lock")
        time.sleep(0.3)
    if waiter_count()<2:
        raise AssertionError("Two PostgreSQL sessions were not simultaneously blocked")
    print("FEATURE2_AI_BUDGET_TWO_REAL_LOCK_WAITERS=PASS",flush=True)

    code_l, out_l, err_l=finish(locker,"Subscription locker",timeout=30)
    if code_l:
        raise AssertionError("Subscription lock holder failed: "+err_l[-500:])
    outcomes=[finish(first,"First reservation"),finish(second,"Second reservation")]
    wins=[o for o in outcomes if o[0]==0]
    losses=[o for o in outcomes if o[0]!=0]
    if len(wins)!=1 or len(losses)!=1:
        raise AssertionError("Expected exactly one allowed reservation, one rejected")
    if ("F2_RECEIPT:" not in wins[0][1] or
        "AI_QUOTA_EXCEEDED" not in losses[0][2]):
        raise AssertionError("Unexpected budget race winner/loser contract")
    result=call(
        "select json_build_object("
        "'count',(select count(*) from public.shop_ai_spend_reservations "
        f"where shop_id='{SHOP}'),"
        "'sum',(select coalesce(sum(reserved_usd),0) from "
        f"public.shop_ai_spend_reservations where shop_id='{SHOP}'),"
        "'period_cap',(select period_cap_usd from public.shop_ai_budget_controls "
        f"where shop_id='{SHOP}')"
        ")::text;")
    result_json=json.loads(result.stdout.strip().splitlines()[-1])
    if (result_json["count"]!=1 or float(result_json["sum"])!=0.003
        or float(result_json["period_cap"])!=0.004):
        raise AssertionError("Concurrent calls bypassed period budget: "+str(result_json))
    # psql -c containing multiple commands can return 1 rather than 3 on
    # deliberate SQL failure. Verify SQLSTATE/message, not only exit code.
    # The winner is nondeterministic under genuine concurrent PostgreSQL locks.
    # Replay the WINNER'S same request UUID; the loser uses a distinct UUID.
    winner_nonce = ("f2d00000-0000-4000-8000-000000000011"
                    if outcomes[0][0] == 0 else
                    "f2d00000-0000-4000-8000-000000000012")
    again=call(req(winner_nonce),application="f2-budget-race-lost-ack",allowed=(0,1,3))
    if again.returncode==0 or "AI_REQUEST_ALREADY_RESERVED" not in again.stderr:
        raise AssertionError("Repeated paid model POST after lost acknowledgement double-reserved")
    print("FEATURE2_AI_BUDGET_CONCURRENT_CAP_AND_LOST_ACK=PASS",flush=True)
    print("FEATURE2_AI_BUDGET_NO_HOSTED_WRITES_NO_INFERENCE=PASS",flush=True)


if __name__=="__main__":
    try:
        check()
    except (AssertionError, subprocess.SubprocessError, ValueError,
            json.JSONDecodeError, KeyError) as exc:
        print("FAIL: "+str(exc),file=sys.stderr)
        sys.exit(1)
    finally:
        for child in CHILDREN:
            if child.poll() is None:
                child.terminate()
                try: child.communicate(timeout=4)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()
