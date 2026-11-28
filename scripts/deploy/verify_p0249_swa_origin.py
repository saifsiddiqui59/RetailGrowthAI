#!/usr/bin/env python3
"""Read-only public DEV SWA asset graph verification for Y1 cutover/rollback.

This is deployed-artifact evidence, not signed browser/API/worker acceptance.
No deployment, credentials, Azure management calls or customer data.
"""
from __future__ import annotations

import argparse
import re
import urllib.request
from html.parser import HTMLParser

FRONTEND = "https://purple-dune-06b5da200.2.azurestaticapps.net"
Y1 = "https://rgai-dev-y1-p0249-d4e5ddbd.azurewebsites.net"
FLEX = "https://rgai-dev-functions-d4e5ddbd.azurewebsites.net"
ROUTES = (
    "/",
    "/business",
    "/campaigns",
    "/trends",
    "/testing-chat",
    "/subscription",
    "/calendar",
    "/creative-studio",
    "/media-library",
    "/connections",
    "/publishing",
    "/notifications",
    "/settings",
    "/platform-admin",
    "/platform-alerts",
    "/account",
)
ASSET = re.compile(r"/assets/[A-Za-z0-9_-]+-[A-Za-z0-9_-]+\.js")
REFERENCES = re.compile(r"""['"](?:\./|/assets/|assets/)([A-Za-z0-9_-]+-[A-Za-z0-9_-]+\.js)['"]""")
AZURE_ORIGIN = re.compile(r"(?<![A-Za-z0-9+.-])(?:https?:)?//[A-Za-z0-9.-]+\.azurewebsites\.net(?::[0-9]+)?(?=[/:?#'\x22\s]|$)", re.I)
MAX_ASSETS = 128
MAX_ASSET_BYTES = 8_000_000
MAX_TOTAL_BYTES = 64_000_000


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.root = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id") == "root":
            self.root = True
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "modulepreload" and attrs.get("href"):
            self.assets.append(attrs["href"])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(path):
    if path not in ROUTES and not ASSET.fullmatch(path):
        raise ValueError("UNAPPROVED_SWA_PATH")
    req = urllib.request.Request(FRONTEND + path, headers={"Cache-Control": "no-cache"})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as result:
        if result.status != 200 or result.geturl() != FRONTEND + path:
            raise RuntimeError("SWA_WRONG_ORIGIN_OR_STATUS")
        mime = result.headers.get_content_type()
        allowed = {"text/html"} if path in ROUTES else {"application/javascript", "text/javascript"}
        if mime not in allowed:
            raise RuntimeError("SWA_UNEXPECTED_CONTENT_TYPE")
        body = result.read(MAX_ASSET_BYTES + 1)
    if len(body) > MAX_ASSET_BYTES:
        raise RuntimeError("SWA_ASSET_TOO_LARGE")
    return body.decode("utf-8")


def verify(expected, read=fetch):
    if expected not in (Y1, FLEX):
        raise ValueError("UNAPPROVED_EXPECTED_API_ORIGIN")
    pending = set()
    route_entries = None
    total = 0
    for route in ROUTES:
        html = read(route)
        if not isinstance(html, str):
            raise RuntimeError("SWA_INVALID_HTML")
        html_bytes = len(html.encode("utf-8"))
        total += html_bytes
        if html_bytes > MAX_ASSET_BYTES or total > MAX_TOTAL_BYTES:
            raise RuntimeError("SWA_ASSET_GRAPH_SIZE_LIMIT")
        parser = Scripts()
        parser.feed(html)
        entries = {p for p in parser.assets if ASSET.fullmatch(p)}
        if not parser.root or not entries or any(not ASSET.fullmatch(p) for p in parser.assets):
            raise RuntimeError("SWA_ENTRY_INVALID")
        if route_entries is None:
            route_entries = entries
        elif route_entries != entries:
            raise RuntimeError("SWA_INCONSISTENT_ROUTE_BUILD")
        pending.update(entries)
    seen = set()
    found = set()
    while pending:
        if len(seen) >= MAX_ASSETS:
            raise RuntimeError("SWA_ASSET_GRAPH_LIMIT")
        path = min(pending)
        pending.remove(path)
        if path in seen:
            continue
        data = read(path)
        if not isinstance(data, str):
            raise RuntimeError("SWA_INVALID_JAVASCRIPT")
        size = len(data.encode("utf-8"))
        total += size
        if size > MAX_ASSET_BYTES or total > MAX_TOTAL_BYTES:
            raise RuntimeError("SWA_ASSET_GRAPH_SIZE_LIMIT")
        seen.add(path)
        # No old, foreign, HTTP or mixed Functions origin in any reachable chunk.
        found.update(m.group(0).lower() for m in AZURE_ORIGIN.finditer(data))
        pending.update("/assets/" + f for f in REFERENCES.findall(data)
                       if "/assets/" + f not in seen)
    if found != {expected}:
        raise RuntimeError("SWA_API_ORIGIN_ABSENT_MIXED_OR_FOREIGN")
    return len(seen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", required=True, choices=("y1", "flex"))
    args = parser.parse_args()
    try:
        count = verify(Y1 if args.expected == "y1" else FLEX)
        print("P0249_SWA_SERVED_API_ORIGIN=" + args.expected.upper() + "_ASSET_GRAPH_PASS")
        print("P0249_SWA_VERIFIED_JS_ASSET_COUNT=" + str(count))
        print("P0249_SWA_SIGNED_RUNTIME_ACCEPTANCE=false")
    except Exception:
        # Never print public bundle bytes, injected URL, token, or raw exception.
        print("P0249_SWA_SERVED_API_ORIGIN=BLOCKED")
        raise SystemExit(2)
