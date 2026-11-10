#!/usr/bin/env python3
"""Real two-connection Reel RPC idempotency gate, DISPOSABLE local Postgres ONLY.

Run only from GitHub Actions' Supabase security job, after migrations and the
transaction-rolled-back poster_reel_intent_negative.sql have passed.
No requests, credentials, or writes are made against hosted DEV/PROD.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CAMPAIGN = "a4444444-4444-4444-8444-444444444444"
DAY = "a8888888-8888-4888-8888-888888888888"
ACTOR = "a1111111-1111-4111-8111-111111111111"
SHOP = "a3333333-3333-4333-8333-333333333333"
ROOT = Path(__file__).resolve().parents[2]

# The marker must be set explicitly in the coordinator-owned CI job. Guard
# against accidental invocation on any real database, even with a local proxy.
if (
    os.environ.get("RETAIL_DISPOSABLE_POSTGRES") != "1"
    or os.environ.get("PGHOST") != "127.0.0.1"
    or os.environ.get("PGPORT") != "54322"
    or os.environ.get("PGDATABASE") != "postgres"
    or os.environ.get("PGUSER") != "postgres"
    or not os.environ.get("PGPASSWORD")
):
    raise SystemExit("REFUSED: requires explicitly flagged disposable local Supabase Postgres")

BASE = ["psql", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1"]
CHILDREN = []


def run_sql(sql: str, app: str = "rga-reel-race-check") -> str:
    env = dict(os.environ, PGAPPNAME=app)
    result = subprocess.run(
        [*BASE, "-c", sql], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode:
        raise AssertionError(f"psql {app} failed: {result.stderr[-1200:]}")
    return result.stdout.strip()


def start(sql: str, app: str) -> subprocess.Popen:
    child = subprocess.Popen(
        [*BASE, "-c", sql],
        cwd=ROOT, env=dict(os.environ, PGAPPNAME=app),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    CHILDREN.append(child)
    return child


def finish(child: subprocess.Popen, label: str, timeout=25) -> str:
    try:
        out, err = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"{label} timed out waiting for SQL lock") from exc
    if child.returncode != 0:
        raise AssertionError(f"{label} failed: {err[-1200:]}")
    return out


def result_job_id(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("RGA_RESULT:"):
            data = json.loads(line.removeprefix("RGA_RESULT:"))
            if data.get("status") not in {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED"}:
                raise AssertionError(f"unexpected returned job state: {data}")
            return data["job_id"]
    raise AssertionError(f"Reel RPC did not return a job: {output[-500:]}")


def count_waiters() -> int:
    return int(run_sql(
        "select count(*) from pg_catalog.pg_stat_activity "
        "where application_name in ('rga-reel-race-a','rga-reel-race-b') "
        "and wait_event_type='Lock';"
    ).splitlines()[-1])


def main() -> None:
    print("START: isolated two-session Reel RPC lock/idempotency check")
    subprocess.run(
        [*BASE, "-f", "tests/security/reel_intent_concurrency_setup.sql"],
        cwd=ROOT, env=dict(os.environ, PGAPPNAME="rga-reel-race-setup"),
        capture_output=True, text=True, check=True, timeout=45,
    )
    # Hold the *same campaign row* locked by the RPC while two separately
    # authenticated connections contend. This proves they actually overlap,
    # rather than merely issuing two sequential HTTP requests.
    locker = start(
        "begin; select id from public.campaigns "
        f"where id='{CAMPAIGN}' for update; select pg_sleep(16); commit;",
        "rga-reel-race-locker",
    )
    time.sleep(1)
    if locker.poll() is not None:
        raise AssertionError("campaign lock holder exited prematurely")

    request = (
        "begin; set local role authenticated; "
        f"select set_config('request.jwt.claims',"
        f"'{{\"role\":\"authenticated\",\"sub\":\"{ACTOR}\",\"is_anonymous\":false}}',true); "
        "select 'RGA_RESULT:' || "
        f"public.request_reel_render_job('{CAMPAIGN}','{DAY}')::text; "
        "commit;"
    )
    first = start(request, "rga-reel-race-a")
    second = start(request, "rga-reel-race-b")
    deadline = time.monotonic() + 11
    while count_waiters() < 2 and time.monotonic() < deadline:
        if first.poll() is not None or second.poll() is not None:
            culprit = first if first.poll() is not None else second
            output, error = culprit.communicate(timeout=2)
            raise AssertionError(
                "a contender completed before both were blocked "
                f"(exit={culprit.returncode}, stdout={output[-350:]!r}, stderr={error[-350:]!r})"
            )
        time.sleep(0.4)
    if count_waiters() < 2:
        raise AssertionError("did not observe TWO actual DB connections waiting on the row lock")
    print("PASS: two distinct authenticated SQL sessions simultaneously blocked on campaign row")

    finish(locker, "locker", timeout=25)
    job1 = result_job_id(finish(first, "first waiter"))
    job2 = result_job_id(finish(second, "second waiter"))
    if job1 != job2:
        raise AssertionError("simultaneous identical intent created two jobs")

    # Lost acknowledgement retry in an independent fresh connection.
    again = result_job_id(run_sql(request, "rga-reel-race-lost-ack"))
    if again != job1:
        raise AssertionError("lost-ACK request did not reuse original job")

    result = json.loads(run_sql(
        "select pg_catalog.json_build_object("
        "'jobs',(select count(*) from public.render_jobs "
        f"where shop_id='{SHOP}' and campaign_id='{CAMPAIGN}'),"
        "'quota',(select count(*) from public.shop_usage_reservations "
        f"where shop_id='{SHOP}' and operation='render'),"
        "'outbox',(select count(*) from public.job_outbox o "
        "join public.render_jobs j on j.id=o.job_id "
        f"where j.shop_id='{SHOP}' and j.campaign_id='{CAMPAIGN}' and o.kind='render')"
        ")::text;"
    ).splitlines()[-1])
    if result != {"jobs": 1, "quota": 1, "outbox": 1}:
        raise AssertionError(f"concurrency broke atomic job/usage/outbox: {result}")
    print("PASS: two simultaneous requests + lost ACK => one job, one quota, one outbox")
    print("NOTE: disposable database is destroyed by the existing CI teardown; no hosted writes")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        for child in CHILDREN:
            if child.poll() is None:
                child.terminate()
                try:
                    child.communicate(timeout=4)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()
