#!/usr/bin/env python3
"""Read-only verification of RetailGrowthAI's existing Free SWA lazy Feature2 route.

The authenticated React /trends route is lazy-loaded: its user-visible strings
are in TrendWorkspace-<hash>.js, NOT in the index-<hash>.js entry bundle.
Checks the served HTTPS SPA AND the actual resolved, hashed lazy asset. No secrets,
cloud control-plane calls, browser login, cookies, mutations, or paid services.
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

HOST = "purple-dune-06b5da200.2.azurestaticapps.net"
BASE = "https://" + HOST
MESSAGE = "Create a standard campaign without a trend"
INDEX_JS = re.compile(r"/assets/index-[A-Za-z0-9_-]+\.js")
LAZY_JS = re.compile(r"TrendWorkspace-[A-Za-z0-9_-]+\.js")


class _ScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            source = dict(attrs).get("src")
            if isinstance(source, str):
                self.sources.append(source)


def find_entry_js(index_html: str) -> str:
    """Require exactly one Vite origin-relative index bundle, no injected CDN."""
    parser = _ScriptParser()
    parser.feed(index_html)
    matching = [src for src in parser.sources if INDEX_JS.fullmatch(src)]
    if len(matching) != 1:
        raise ValueError("Expected one Vite entry script in live SPA")
    return matching[0]


def find_lazy_trends_js(entry_source: str) -> str:
    """Get one hashed chunk filename actually referenced by the live main JS."""
    matches = set(LAZY_JS.findall(entry_source))
    if len(matches) != 1:
        raise ValueError("Live JS must reference exactly one lazy Feature2 trends chunk")
    return "/assets/" + matches.pop()


def verify_lazy_text(route_source: str) -> None:
    if MESSAGE not in route_source:
        raise ValueError("New honest Feature2 fallback is absent from the served route chunk")
    if "trend_id: evergreen" in route_source:
        raise ValueError("Forbidden fabricated trend identifier")


def _fetch(path: str) -> str:
    if path not in ("/trends", "/campaigns") and not (
        INDEX_JS.fullmatch(path) or re.fullmatch(r"/assets/TrendWorkspace-[A-Za-z0-9_-]+\.js", path)
    ):
        raise ValueError("Refusing untrusted URL path")
    request = urllib.request.Request(
        BASE + path, headers={"Accept": "text/html,application/javascript", "Cache-Control": "no-cache"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        actual = urllib.parse.urlsplit(response.geturl())
        if actual.scheme != "https" or actual.netloc != HOST or response.status != 200:
            raise RuntimeError("Unexpected HTTPS origin, redirect, or response status")
        content = response.read(2_000_001)
    if len(content) > 2_000_000:
        raise RuntimeError("Unexpectedly large public SPA or JS asset")
    return content.decode("utf-8")


def verify_hosted(max_attempts: int = 8) -> bool:
    """Retry bounded eventual consistency only on safe public GET; never mutate."""
    for attempt in range(max_attempts):
        try:
            trends = _fetch("/trends")
            campaigns = _fetch("/campaigns")
            if 'id="root"' not in trends or 'id="root"' not in campaigns:
                raise RuntimeError("Public SPA route did not return React root")
            entry = find_entry_js(trends)
            lazy = find_lazy_trends_js(_fetch(entry))
            verify_lazy_text(_fetch(lazy))
            print("FEATURE2_FREE_SWA_VERIFIED_LAZY_ROUTE=true")
            print("FEATURE2_FREE_SWA_PUBLIC_ROUTES=true")
            return True
        except (RuntimeError, ValueError, OSError, UnicodeError) as exc:
            if attempt == max_attempts - 1:
                raise RuntimeError("Verified live lazy Feature2 JS not served") from exc
            time.sleep(4)
    return False


if __name__ == "__main__":
    verify_hosted()
