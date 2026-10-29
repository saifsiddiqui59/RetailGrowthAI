"""Local operator Playwright helper for the existing protected RetailGrowthAI DEV canary.

Run this BEFORE manually dispatching node-poster-reel from GitHub Actions.
This script uses the actual authenticated ROOT UI, never service-role SQL/JWT,
and approves only two new disposable rgai-canary-<12hex>-[ab]@example.invalid
requests originating AFTER the operator started watching. It will not
approve pre-existing users, ordinary customers, other domains or other runs.

Run locally on an Internet-connected operator computer, NOT GitHub CI:
  uv run --with playwright python -m playwright install chromium
  uv run --with playwright python scripts/ops/p0249_root_canary_playwright.py --approve-test-only
The script prompts for email and password securely (never placed in argv/logs).
"""
from __future__ import annotations

import argparse
import getpass
import re
import subprocess
import sys
import time

DEV_ORIGIN = "https://purple-dune-06b5da200.2.azurestaticapps.net"
CANARY_RE = re.compile(r"^rgai-canary-([0-9a-f]{12})-([ab])@example\.invalid$", re.ASCII)
DECISION_REASON = "Owner-authorized isolated DEV temporary two-shop canary E2E acceptance"


def eligible_canary(email: str, baseline: set[str], prefix: str | None) -> bool:
    """Never select an existing, foreign, non-canary or mismatched-run account."""
    match = CANARY_RE.fullmatch(email)
    if not match or email in baseline:
        return False
    if prefix is None:
        return match.group(2) == "a"
    return match.group(1) == prefix and match.group(2) == "b"


def read_pending(page) -> set[str]:
    """Use the same ROOT-only React approval queue used by a human operator."""
    return set(page.locator(".platform-review-item strong").all_inner_texts())


def is_onboarding_queue_reply(response) -> bool:
    """Identify only the real authenticated ROOT queue RPC response."""
    from urllib.parse import urlsplit
    url = urlsplit(response.url)
    return (url.scheme == "https"
            and url.hostname == "jeearzffnjbvghwjjjrf.supabase.co"
            and url.path == "/rest/v1/rpc/retail_platform_onboarding_requests"
            and response.request.method == "POST")


def refresh_pending(page) -> set[str]:
    # A hidden loading spinner alone is NOT a sync barrier: React may not
    # mount the pending state until after the original click returns. Wait
    # for the actual signed platform API reply before inspecting DOM rows.
    with page.expect_response(is_onboarding_queue_reply, timeout=15_000) as result:
        page.get_by_role("button", name="Refresh queue").click()
    response = result.value
    if not response.ok:
        raise RuntimeError("ROOT approval queue HTTP request failed; no decisions made")
    page.get_by_text("Loading pending retailer requests…", exact=True).wait_for(
        state="hidden", timeout=15_000)
    # React's resolved Promise updates the row state on a subsequent render.
    # Give it one browser event-loop turn, never read stale rows immediately
    # from a response event that fires before its React Promise settles.
    page.wait_for_timeout(100)
    error = page.locator(".platform-approvals [role='alert']")
    if error.count():
        raise RuntimeError("ROOT approval queue failed to load; no decisions made")
    return read_pending(page)


def approve_exact_row(page, email: str) -> None:
    """Interact with the audited ROOT approval form; no REST/SQL shortcuts."""
    rows = page.locator(".platform-review-item")
    matching = rows.filter(has=page.locator("strong", has_text=email))
    if matching.count() != 1 or matching.locator("strong").inner_text() != email:
        raise RuntimeError("Requested synthetic account is not uniquely visible")
    matching.get_by_role("button", name="Review account").click()
    matching.get_by_label("Decision reason").fill(DECISION_REASON)
    matching.get_by_role("checkbox", name="I verified this account request and authorize the decision.").check()
    matching.get_by_role("button", name="Approve", exact=True).click()
    matching.wait_for(state="detached", timeout=15_000)
    if page.get_by_text("Retailer onboarding approved.", exact=True).count() == 0:
        raise RuntimeError("No audited UI approval confirmation; stop without retry")


def dispatch_owner_approved_dev_canary() -> None:
    """Optional explicit operator gh dispatch, after ROOT UI is fully ARMED.

    This uses the operator's *existing* GitHub CLI authentication; no access
    token, test password or Supabase service key is supplied or stored.
    The GitHub workflow keeps its protected DEV environment and ROOT gate.
    """
    try:
        subprocess.run([
            "gh", "workflow", "run", "retail-dev-test-accounts-canary-once.yml",
            "--repo", "saifsiddiqui59/RetailGrowthAI", "--ref", "main",
            "-f", "approval_code=AUTHORIZED_RETAILGROWTHAI_DEV_ONLY",
            "-f", "mode=node-poster-reel",
        ], check=True, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Protected DEV workflow dispatch failed; check gh auth and repo access") from exc
    print("Protected node-poster-reel workflow was intentionally dispatched.", flush=True)


def operator_run(page, email: str, password: str, poll_seconds: float = 4,
                 max_seconds: int = 650, dispatch: bool = False) -> None:
    page.goto(DEV_ORIGIN + "/platform-admin", wait_until="domcontentloaded", timeout=30_000)
    # Wait for React to mount before deciding whether this is an existing ROOT
    # session or the normal sign-in page (domcontentloaded alone is too early).
    page.locator(".login-screen, .platform-approvals, [aria-label=\'Platform access denied\']").first.wait_for(
        state="visible", timeout=30_000)
    login = page.get_by_role("button", name="Sign in", exact=True)
    if login.count():
        page.get_by_label("Email", exact=True).fill(email)
        page.get_by_label("Password", exact=True).fill(password)
        login.click()
    # An authenticated non-ROOT account fails here; never grant ROOT via SQL.
    page.get_by_role("heading", name="Retailer signup approvals").wait_for(timeout=30_000)
    page.get_by_role("button", name="Review requests").click()
    baseline = refresh_pending(page)
    print("ARMED: ROOT authenticated. Start the GitHub node-poster-reel manual DEV canary now.", flush=True)
    print("Previously pending accounts excluded: " + str(len(baseline)), flush=True)
    if dispatch:
        dispatch_owner_approved_dev_canary()
    deadline = time.monotonic() + max_seconds
    prefix: str | None = None
    approved: set[str] = set()
    while time.monotonic() < deadline:
        pending = refresh_pending(page)
        candidates = sorted(e for e in pending
                            if eligible_canary(e, baseline | approved, prefix))
        if candidates:
            target = candidates[0]
            found = CANARY_RE.fullmatch(target)
            assert found is not None
            approve_exact_row(page, target)
            approved.add(target)
            if prefix is None:
                prefix = found.group(1)
            print("ROOT UI approved disposable canary retailer " + found.group(2).upper(), flush=True)
            if len(approved) == 2:
                print("CANARY_BOTH_ROOT_UI_APPROVALS_COMPLETE=true", flush=True)
                return
        page.wait_for_timeout(max(1000, int(poll_seconds * 1000)))
    raise RuntimeError("Timed out; no non-canary or older account was approved")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ROOT-only local Playwright two-shop DEV canary approvals")
    parser.add_argument("--approve-test-only", action="store_true",
                        help="Explicitly permit only fresh synthetic example.invalid [ab] canary UI approvals")
    parser.add_argument("--headless", action="store_true",
                        help="Use headless Chromium; default shows the browser for human oversight")
    parser.add_argument("--dispatch-dev-canary", action="store_true",
                        help="Once ROOT UI is armed, intentionally start protected GitHub node-poster-reel via gh CLI")
    args = parser.parse_args(argv)
    if not args.approve_test_only:
        parser.error("Pass --approve-test-only explicitly; this command makes audited ROOT decisions")
    email = input("DEV ROOT email: ").strip()
    password = getpass.getpass("DEV ROOT password (not echoed or stored): ")
    if not email or not password:
        raise RuntimeError("ROOT credentials required; no guest/admin bypass")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install Playwright: uv run --with playwright ...") from exc
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        try:
            context = browser.new_context(accept_downloads=False)
            page = context.new_page()
            operator_run(page, email, password, dispatch=args.dispatch_dev_canary)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never dump browser tracebacks, response headers, cookies or credentials.
        print("DEV operator Playwright approval stopped; check ROOT session and live canary.", file=sys.stderr)
        sys.exit(1)
