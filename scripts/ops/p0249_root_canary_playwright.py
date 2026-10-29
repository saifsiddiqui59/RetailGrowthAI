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


def choose_pending_candidate(pending: set[str], baseline: set[str],
                             approved: set[str], prefix: str | None) -> str | None:
    """Reject ambiguous parallel canary A runs instead of approving a stranger's test."""
    candidates = sorted(e for e in pending
                        if eligible_canary(e, baseline | approved, prefix))
    if not candidates:
        return None
    if prefix is None and len(candidates) != 1:
        raise RuntimeError("Multiple fresh canary runs visible; no ROOT decisions made")
    return candidates[0]


def read_pending(page) -> set[str]:
    """Use the same ROOT-only React approval queue used by a human operator."""
    return set(page.locator(".platform-review-item strong").all_inner_texts())


def is_onboarding_queue_request(request) -> bool:
    """Match only a new request to the real DEV signed ROOT list RPC."""
    from urllib.parse import urlsplit
    url = urlsplit(request.url)
    return (url.scheme == "https"
            and url.hostname == "jeearzffnjbvghwjjjrf.supabase.co"
            and url.path == "/rest/v1/rpc/retail_platform_onboarding_requests"
            and request.method == "POST")


def is_onboarding_queue_reply(response) -> bool:
    """Retain response validation for a request's own completed HTTP reply."""
    return (is_onboarding_queue_request(response.request)
            and response.url == response.request.url)


def pending_response_for_click(page, button_name: str):
    # Await a REQUEST initiated AFTER this specific button click, not the
    # RESPONSE from an older in-flight queue load with an identical URL.
    with page.expect_request(is_onboarding_queue_request, timeout=15_000) as result:
        page.get_by_role("button", name=button_name).click()
    request = result.value
    response = request.response()
    if response is None or not is_onboarding_queue_reply(response) or not response.ok:
        raise RuntimeError("ROOT approval queue HTTP request failed; no decisions made")
    return response


def verified_pending_rows(page, response) -> set[str]:
    # An HTTP reply is not a React render barrier. Parse only the exact
    # request's successful ROOT response, then match displayed rows to it.
    try:
        items = response.json()
    except (ValueError, TypeError) as exc:
        raise RuntimeError("ROOT queue response is not valid JSON") from exc
    from uuid import UUID
    def valid_user_id(value):
        if not isinstance(value, str):
            return False
        try:
            parsed = UUID(value)
        except ValueError:
            return False
        return parsed.version == 4 and str(parsed) == value

    if not isinstance(items, list) or len(items) > 40 or any(
        not isinstance(item, dict)
        or not isinstance(item.get("email"), str)
        or not item["email"]
        or not valid_user_id(item.get("user_id"))
        for item in items
    ):
        raise RuntimeError("ROOT queue response has invalid email/user mapping")
    expected = [item["email"] for item in items]
    user_ids = [item["user_id"] for item in items]
    if len(set(expected)) != len(expected) or len(set(user_ids)) != len(user_ids):
        raise RuntimeError("ROOT queue contains duplicate identities; no decisions made")
    page.get_by_text("Loading pending retailer requests…", exact=True).wait_for(
        state="hidden", timeout=15_000)
    # Current React component uses RPC array order; fixed sleeps can still
    # show the older list when an initial and refresh fetch overlap.
    page.wait_for_function(
        """expected => {
          const root = document.querySelector('.platform-approvals');
          if (!root || root.querySelector('[role="alert"]')) return false;
          const loading = [...root.querySelectorAll('[role="status"]')]
            .some(node => node.textContent.includes('Loading pending retailer requests'));
          const shown = [...root.querySelectorAll('.platform-review-item strong')]
            .map(node => node.textContent.trim());
          return !loading && shown.length === expected.length
            && shown.every((email, index) => email === expected[index]);
        }""",
        arg=expected, timeout=15_000,
    )
    if read_pending(page) != set(expected):
        raise RuntimeError("Rendered ROOT queue differs from verified response")
    return {item["email"]: item["user_id"] for item in items}


def open_pending_queue(page) -> dict[str, str]:
    """Fully synchronize the initial ROOT list before first refresh."""
    return verified_pending_rows(page, pending_response_for_click(page, "Review requests"))


def refresh_pending(page) -> dict[str, str]:
    """Match the refresh button's OWN request, response and rendered rows."""
    return verified_pending_rows(page, pending_response_for_click(page, "Refresh queue"))


def is_onboarding_approval_request(request) -> bool:
    """Only the audited DEV ROOT decision RPC, never another POST."""
    from urllib.parse import urlsplit
    url = urlsplit(request.url)
    return (url.scheme == "https"
            and url.hostname == "jeearzffnjbvghwjjjrf.supabase.co"
            and url.path == "/rest/v1/rpc/retail_platform_review_onboarding"
            and request.method == "POST")


def verified_approval_reply(request, expected_user_id: str):
    """A UI toast alone cannot attest which audited approval was accepted."""
    from uuid import UUID
    if not is_onboarding_approval_request(request):
        raise RuntimeError("Wrong ROOT decision RPC; stop without retry")
    try:
        body = request.post_data_json
        user_id = body["p_user_id"]
        if (not isinstance(body, dict) or set(body) !=
                {"p_user_id", "p_approve", "p_reason"}
                or body["p_approve"] is not True
                or body["p_reason"] != DECISION_REASON
                or not isinstance(user_id, str)
                or UUID(user_id).version != 4
                or str(UUID(user_id)) != user_id
                or user_id != expected_user_id):
            raise ValueError("invalid approval request")
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Audited ROOT approval request mismatch; stop without retry") from exc
    reply = request.response()
    if reply is None or reply.request != request or not reply.ok:
        raise RuntimeError("ROOT approval HTTP result uncertain; stop without retry")
    return reply


def approve_exact_row(page, email: str, expected_user_id: str) -> None:
    """Interact with the audited ROOT approval form; no REST/SQL shortcuts."""
    rows = page.locator(".platform-review-item")
    matching = rows.filter(has=page.locator("strong", has_text=email))
    if matching.count() != 1 or matching.locator("strong").inner_text() != email:
        raise RuntimeError("Requested synthetic account is not uniquely visible")
    matching.get_by_role("button", name="Review account").click()
    matching.get_by_label("Decision reason").fill(DECISION_REASON)
    matching.get_by_role("checkbox", name="I verified this account request and authorize the decision.").check()
    # Bind the button's own request to its accepted response. Never retry a
    # possibly committed privileged decision after a missing/failed HTTP ACK.
    with page.expect_request(is_onboarding_approval_request, timeout=15_000) as decision:
        matching.get_by_role("button", name="Approve", exact=True).click()
    verified_approval_reply(decision.value, expected_user_id)
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
    baseline = set(open_pending_queue(page))
    print("ARMED: ROOT authenticated. Start the GitHub node-poster-reel manual DEV canary now.", flush=True)
    print("Previously pending accounts excluded: " + str(len(baseline)), flush=True)
    if dispatch:
        dispatch_owner_approved_dev_canary()
    deadline = time.monotonic() + max_seconds
    prefix: str | None = None
    approved: set[str] = set()
    while time.monotonic() < deadline:
        pending = refresh_pending(page)
        target = choose_pending_candidate(pending, baseline, approved, prefix)
        if target:
            found = CANARY_RE.fullmatch(target)
            assert found is not None
            approve_exact_row(page, target, pending[target])
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
