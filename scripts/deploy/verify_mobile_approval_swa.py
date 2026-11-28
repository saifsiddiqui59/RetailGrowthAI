#!/usr/bin/env python3
"""Read-only checks of the existing DEV SWA and deployed reviewed assets."""
import argparse
import hashlib
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

HOST = "https://purple-dune-06b5da200.2.azurestaticapps.net"
FLEX = "https://rgai-dev-functions-d4e5ddbd.azurewebsites.net"
ROUTES = ("/platform-admin", "/account", "/campaigns")
ASSET = re.compile(r"/assets/[A-Za-z0-9_-]+-[A-Za-z0-9_-]+\.(?:js|css)")
REF = re.compile(r"""['"](?:\./|/assets/|assets/)?([A-Za-z0-9_-]+-[A-Za-z0-9_-]+\.(?:js|css))['"]""")
ORIGIN = re.compile(r"https?://[A-Za-z0-9.-]+\.azurewebsites\.net", re.I)
LIMIT = 8_000_000
HINT = b"Tick the confirmation above to enable Approve and Reject."
CSS_MARKER = b".platform-review-confirm"

class Html(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = False
        self.assets = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.root |= a.get("id") == "root"
        path = a.get("src") if tag == "script" else a.get("href") if tag == "link" else None
        if path and ASSET.fullmatch(path):
            self.assets.add(path)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def read(path):
    if path not in ROUTES and not ASSET.fullmatch(path):
        raise ValueError("UNAPPROVED_PATH")
    req = urllib.request.Request(HOST + path, headers={"Cache-Control":"no-cache"})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
        if response.status != 200 or response.geturl() != HOST + path:
            raise RuntimeError("WRONG_SWA_ORIGIN")
        data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise RuntimeError("ASSET_TOO_LARGE")
        return data

def verify(fetch=read, dist=None):
    entry = None
    for route in ROUTES:
        parser = Html()
        parser.feed(fetch(route).decode("utf-8"))
        if not parser.root or not any(p.endswith(".js") for p in parser.assets):
            raise RuntimeError("SPA_ENTRY_MISSING")
        if entry is not None and entry != parser.assets:
            raise RuntimeError("MIXED_ROUTE_BUILD")
        entry = parser.assets
    pending = set(entry)
    seen = set()
    origins = set()
    total = 0
    hint = css = False
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if len(seen) >= 160:
            raise RuntimeError("ASSET_GRAPH_LIMIT")
        data = fetch(path)
        total += len(data)
        if len(data) > LIMIT or total > 80_000_000:
            raise RuntimeError("ASSET_GRAPH_SIZE_LIMIT")
        seen.add(path)
        origins.update(x.lower() for x in ORIGIN.findall(data.decode("utf-8")))
        if dist is not None:
            expected = (Path(dist) / path.lstrip("/")).read_bytes()
            if hashlib.sha256(data).digest() != hashlib.sha256(expected).digest():
                raise RuntimeError("DEPLOYED_ASSET_BYTES_DIFFER")
            hint |= path.endswith(".js") and HINT in data
            css |= path.endswith(".css") and CSS_MARKER in data and b"grid-template-columns:minmax(0,1fr)" in data
        pending.update("/assets/" + f for f in REF.findall(data.decode("utf-8")) if "/assets/" + f not in seen)
    if origins != {FLEX}:
        raise RuntimeError("LIVE_API_ORIGIN_CHANGED_OR_UNKNOWN")
    if dist is not None and not (hint and css):
        raise RuntimeError("MOBILE_FIX_ASSETS_NOT_SERVED")
    return len(seen)

def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--before", action="store_true")
    group.add_argument("--after", action="store_true")
    group.add_argument("--local", action="store_true")
    p.add_argument("--dist", type=Path)
    args = p.parse_args()
    if (args.after or args.local) != bool(args.dist):
        p.error("--after/--local require --dist; --before forbids it")
    if args.local:
        def read_local(path):
            if path in ROUTES:
                return (args.dist / "index.html").read_bytes()
            if not ASSET.fullmatch(path):
                raise ValueError("UNAPPROVED_PATH")
            return (args.dist / path.lstrip("/")).read_bytes()
        count = verify(fetch=read_local, dist=args.dist)
        print(f"MOBILE_APPROVAL_LOCAL_ASSET_GRAPH=PASS count={count}")
        return
    for attempt in range(3 if args.after else 1):
        try:
            count = verify(dist=args.dist)
            print(f"MOBILE_APPROVAL_ASSET_GRAPH=PASS count={count}")
            return
        except (OSError, RuntimeError, ValueError):
            if not args.after or attempt == 2:
                raise RuntimeError("MOBILE_APPROVAL_PUBLIC_ASSET_CHECK_FAILED") from None
            time.sleep(5)

if __name__ == "__main__":
    main()
