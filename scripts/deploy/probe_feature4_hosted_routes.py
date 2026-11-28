#!/usr/bin/env python3
"""Verify all seven F4 HTTP handlers with anonymous, non-mutating probes.

A handler-marked 401 proves the URL reached an authentication boundary, not
signed access, feature flags, job processing, media rights, or deployment
ownership. Fixed DEV origins, no redirects, no credentials, no POST replay.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from uuid import uuid4

ORIGINS = {
    "original-flex": "https://rgai-dev-functions-d4e5ddbd.azurewebsites.net",
    "isolated-y1": "https://rgai-dev-y1-p0249-d4e5ddbd.azurewebsites.net",
}
ROUTES = (
    ("issue_feature4_creative_plan", "POST", "/api/campaigns/{id}/feature4-plans"),
    ("read_feature4_creative_plan", "GET", "/api/feature4-creative-plans/{id}"),
    ("review_feature4_creative_plan", "POST", "/api/feature4-creative-plans/{id}/review"),
    ("revoke_feature4_creative_plan", "POST", "/api/feature4-creative-plans/{id}/revoke"),
    ("create_feature4_render", "POST", "/api/campaigns/{id}/feature4-renders"),
    ("get_feature4_render", "GET", "/api/feature4-render-jobs/{id}"),
    ("download_feature4_render", "GET", "/api/feature4-render-jobs/{id}/download"),
)


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify(target, opener=None):
    if target not in ORIGINS:
        raise ValueError("unsupported DEV target")
    # No ProxyHandler from environment, no cookies, auth handlers or redirects.
    opener = opener or urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirects())
    outcomes = {}
    for name, method, path in ROUTES:
        req = urllib.request.Request(
            ORIGINS[target] + path.format(id=str(uuid4())),
            data=b"{}" if method == "POST" else None,
            headers={"Accept": "application/json", "Content-Type": "application/json",
                     "Cache-Control": "no-store"}, method=method)
        outcome = "transport_failure"
        try:
            try:
                response = opener.open(req, timeout=25)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                code = response.getcode()
                # Do not output response body, server identifiers or request IDs.
                if code == 401:
                    trace = response.headers.get("X-Request-ID", "")
                    body = response.read(1025)
                    if (re.fullmatch(r"[0-9a-f]{32}", trace)
                            and len(body) <= 1024
                            and json.loads(body) == {"error": "UNAUTHORIZED"}):
                        outcome = "marked_401"
                    else:
                        outcome = "unmarked_or_invalid_401"
                elif code == 404:
                    outcome = "not_found"
                elif code in (502, 503, 504):
                    outcome = "gateway_or_unavailable"
                elif 300 <= code < 400:
                    outcome = "redirect_denied"
                elif 200 <= code < 300:
                    outcome = "unexpected_success"
                else:
                    outcome = "unexpected_status"
        except (OSError, ValueError, TypeError, AttributeError):
            outcome = "transport_or_invalid_response"
        outcomes[name] = outcome
        print(name + "=" + outcome, flush=True)
        # A successful unauthenticated mutation response is a security failure.
        # Stop rather than attempt any additional write-method probes.
        if outcome == "unexpected_success":
            break
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=tuple(ORIGINS))
    args = parser.parse_args()
    outcomes = verify(args.target)
    passed = sum(value == "marked_401" for value in outcomes.values())
    print("F4_HOSTED_ROUTE_AUTH_BOUNDARY=" + str(passed) + "_OF_7")
    print("F4_SIGNED_WORKFLOW_OR_MP4_ACCEPTED=false")
    return 0 if passed == len(ROUTES) == 7 else 1


if __name__ == "__main__":
    raise SystemExit(main())
