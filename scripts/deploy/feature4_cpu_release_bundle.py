#!/usr/bin/env python3
"""Build one all-or-nothing Feature4 CPU DEV SQL candidate from six source files.

SOURCE-ONLY utility. It does not connect to Supabase, apply SQL, provision Azure
resources, waive security review or authorize customer/retailer approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
DEV_PROJECT = "jeearzffnjbvghwjjjrf"
CANDIDATES = (
    "supabase/candidates/feature4_reviewed_cpu_plans_20261121.sql",
    "supabase/candidates/feature4_cpu_render_jobs_20261121.sql",
    "supabase/candidates/feature4_cpu_worker_claim_20261122.sql",
    "supabase/candidates/feature4_cpu_worker_outbox_20261122.sql",
    "supabase/candidates/feature4_cpu_worker_finish_20261122.sql",
    "supabase/candidates/feature4_cpu_worker_poison_20261122.sql",
)
MAX_SOURCE_BYTES = 128_000
START = re.compile(r"(?m)^begin;\s*$", re.IGNORECASE)
END = re.compile(r"(?m)^commit;\s*$", re.IGNORECASE)

PREFLIGHT = """
-- Transactional SQL guard. This is NOT a substitute for verifying the
-- connection's exact Supabase project and independently authorizing release.
do $rgai_f4_preflight$
begin
  if to_regclass('public.shops') is null
     or to_regclass('public.campaigns') is null
     or to_regclass('public.campaign_days') is null
     or to_regclass('public.media_assets') is null
     or to_regclass('public.shop_memberships') is null
     or to_regclass('public.shop_subscriptions') is null
     or to_regclass('public.shop_usage_reservations') is null
     or to_regclass('storage.objects') is null
     or to_regprocedure('retail_private.python_json_v1(jsonb)') is null
     or to_regprocedure('retail_private.has_role(uuid,text[])') is null
     or to_regprocedure('extensions.digest(bytea,text)') is null
  then
    raise exception 'F4 DEV release blocked: required foundation is absent';
  end if;
  if to_regclass('public.feature4_creative_plans') is not null
     or to_regclass('public.feature4_cpu_render_jobs') is not null
     or to_regclass('retail_private.feature4_cpu_outbox') is not null
     or to_regclass('retail_private.feature4_cpu_poison_receipts') is not null
     or to_regprocedure('public.feature4_review_cpu_plan(uuid,text)') is not null
     or to_regprocedure('public.feature4_submit_cpu_render(uuid,text)') is not null
     or to_regprocedure('public.feature4_claim_cpu_render(uuid)') is not null
     or to_regprocedure('public.feature4_complete_cpu_render(uuid,uuid,text,text)') is not null
     or to_regprocedure('public.feature4_record_cpu_poison(text,uuid)') is not null
  then
    raise exception 'F4 DEV release blocked: partially installed schema detected';
  end if;
  if not exists (
       select 1 from pg_catalog.pg_constraint
       where conrelid='public.media_assets'::regclass
         and conname='media_assets_source_check'
         and pg_catalog.pg_get_constraintdef(oid) like '%GENERATED%'
     ) or not exists (
       select 1 from pg_catalog.pg_constraint
       where conrelid='public.shop_usage_reservations'::regclass
         and conname='shop_usage_reservations_operation_check'
         and pg_catalog.pg_get_constraintdef(oid) like '%render%'
     ) then
    raise exception 'F4 DEV release blocked: media or quota baseline mismatch';
  end if;
end $rgai_f4_preflight$;
"""


class ReleaseGuardError(ValueError):
    pass


def _source(root: Path, name: str):
    target = root / name
    if (not target.is_file() or target.is_symlink()
            or any(p.is_symlink() for p in target.parents)):
        raise ReleaseGuardError("Missing or linked source file: " + name)
    if not stat.S_ISREG(target.lstat().st_mode):
        raise ReleaseGuardError("Non-regular source file: " + name)
    raw = target.read_bytes()
    if not raw or len(raw) > MAX_SOURCE_BYTES or b"\0" in raw:
        raise ReleaseGuardError("Invalid or oversized SQL candidate: " + name)
    try:
        value = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseGuardError("Non-UTF8 SQL candidate: " + name) from exc
    begins = list(START.finditer(value))
    ends = list(END.finditer(value))
    if len(begins) != 1 or len(ends) != 1 or begins[0].start() >= ends[0].start():
        raise ReleaseGuardError("Expected exactly one BEGIN/COMMIT pair: " + name)
    leading = value[:begins[0].start()]
    if any(line.strip() and not line.lstrip().startswith("--")
           for line in leading.splitlines()):
        raise ReleaseGuardError("SQL before BEGIN is not allowed: " + name)
    if value[ends[0].end():].strip():
        raise ReleaseGuardError("SQL after COMMIT is not allowed: " + name)
    body = value[begins[0].end():ends[0].start()].strip()
    if not body:
        raise ReleaseGuardError("Empty SQL migration: " + name)
    return body, hashlib.sha256(raw).hexdigest()


def build_bundle(root: Path = ROOT):
    """Return the candidate bundle and its content SHA manifest; never apply."""
    entries = []
    bodies = []
    for name in CANDIDATES:
        body, digest = _source(root, name)
        entries.append({"path": name, "sha256": digest})
        bodies.append("-- SOURCE: " + name + "\n" + body)
    sql = (
        "-- SOURCE-ONLY: protected DEV migration candidate; DO NOT AUTO-APPLY.\n"
        "-- The target project and independent release rights MUST be verified.\n"
        "begin;\n" + PREFLIGHT.strip() + "\n\n"
        + "\n\n".join(bodies) + "\ncommit;\n"
    )
    manifest = {
        "kind": "FEATURE4_CPU_SIX_CANDIDATE_ATOMIC_DEV_BUNDLE_NOT_APPLIED",
        "expected_dev_project": DEV_PROJECT,
        "files": entries,
        "bundle_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "hosted_deployed": False,
    }
    return sql, manifest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-ref", required=True)
    p.add_argument("--output", type=Path, help="Write private offline bundle to a new path")
    args = p.parse_args(argv)
    if args.project_ref != DEV_PROJECT:
        raise SystemExit("BLOCKED: wrong DEV project reference")
    sql, manifest = build_bundle()
    if args.output:
        output = args.output.expanduser().resolve(strict=False)
        if output.is_relative_to(ROOT.resolve()):
            raise SystemExit("BLOCKED: write release bundle outside the checkout")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(output, flags, 0o600)
        with os.fdopen(fd, "wb") as writer:
            writer.write(sql.encode("utf-8"))
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
