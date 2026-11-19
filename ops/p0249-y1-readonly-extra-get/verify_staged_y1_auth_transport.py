"""Offline fail-closed original JWT transport gate before #249 Y1 Azure ZIP.

Verify the ACTUAL allowlisted staged tenant_store.py, never an invented
reimplementation or network endpoint. We temporarily stub only the security
exception import (no JWT or user data), then exercise urllib redirect behavior
against a synthetic in-process HTTPS handler. No Azure, DNS, HTTP, or SQL calls.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
from email.message import Message
from pathlib import Path
import sys
import types
from urllib.request import (HTTPSHandler, HTTPRedirectHandler, OpenerDirector,
                            ProxyHandler, build_opener)
from urllib.response import addinfourl


class GuardError(ValueError):
    pass


def _load_staged_tenant(path: Path):
    """Load exact staged PostgREST transport with ONLY a synthetic auth error.

    A third-party crypto/JWKS client is not needed for this network-denial
    test. The original JWT signature tests run separately; this code never
    verifies real credentials or constructs a Supabase connection.
    """
    stub = types.ModuleType("security")
    stub.AuthenticationError = type("SyntheticAuthError", (ValueError,), {})
    prior = sys.modules.get("security")
    sys.modules["security"] = stub
    try:
        spec = importlib.util.spec_from_file_location(
            "_p0249_y1_staged_tenant_transport", path)
        if spec is None or spec.loader is None:
            raise GuardError("Y1_AUTH_STAGED_SOURCE_UNREADABLE")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if prior is None:
            sys.modules.pop("security", None)
        else:
            sys.modules["security"] = prior


class SyntheticRedirectHTTPS(HTTPSHandler):
    """Emit redirect responses without opening ANY socket."""
    def __init__(self, status: int):
        super().__init__()
        self.status = status
        self.visited = []
        self.responses = []

    def https_open(self, request):
        self.visited.append(request.full_url)
        headers = Message()
        headers["Location"] = "https://untrusted-p0249.invalid/collect"
        response = addinfourl(io.BytesIO(b""), headers, request.full_url,
                              self.status)
        response.msg = "Synthetic Redirect"
        self.responses.append(response)
        return response


def verify_staged_tenant_transport(root: Path) -> None:
    root = root.resolve(strict=True)
    path = root / "tenant_store.py"
    if not path.is_file() or path.is_symlink() or path.resolve() != root / "tenant_store.py":
        raise GuardError("Y1_AUTH_STAGED_SOURCE_UNREADABLE")
    mod = _load_staged_tenant(path)
    redirect_class = getattr(mod, "_RejectRedirects", None)
    if not isinstance(redirect_class, type) or not issubclass(
            redirect_class, HTTPRedirectHandler):
        raise GuardError("Y1_AUTH_REDIRECT_GUARD_NOT_PRESENT")
    store = mod.TenantStore("https://synthetic-p0249.supabase.co",
                            "sb_publishable_synthetic_fixture")
    default_opener = getattr(store.transport, "__self__", None)
    if (not isinstance(default_opener, OpenerDirector)
            or not any(isinstance(handler, redirect_class)
                       for handler in default_opener.handlers)):
        raise GuardError("Y1_AUTH_REDIRECT_GUARD_NOT_DEFAULT")
    for bad in ("http://synthetic-p0249.supabase.co",
                "https://person:password@synthetic-p0249.supabase.co",
                "https://synthetic-p0249.supabase.co/path",
                "https://synthetic-p0249.supabase.co?token=notreal"):
        try:
            mod.TenantStore(bad, "sb_publishable_synthetic_fixture")
        except ValueError:
            continue
        raise GuardError("Y1_AUTH_SUPABASE_ORIGIN_UNSAFE")
    for code in (301, 302, 303, 307, 308):
        responder = SyntheticRedirectHTTPS(code)
        opener = build_opener(ProxyHandler({}), redirect_class(), responder)
        redirected_store = mod.TenantStore(
            "https://synthetic-p0249.supabase.co",
            "sb_publishable_synthetic_fixture", transport=opener.open)
        try:
            redirected_store._request(
                "campaigns", "synthetic.not.a.real.token",
                query={"select": "id"})
        except mod.StorageUnavailable:
            pass
        else:
            raise GuardError("Y1_AUTH_REDIRECT_NOT_REJECTED")
        if responder.visited != [
                "https://synthetic-p0249.supabase.co/rest/v1/campaigns?select=id"]:
            raise GuardError("Y1_AUTH_TOKEN_WOULD_LEAVE_TRUSTED_ORIGIN")
        if len(responder.responses) != 1 or not responder.responses[0].closed:
            raise GuardError("Y1_AUTH_REDIRECT_RESPONSE_NOT_CLOSED")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Y1 JWT transport release gate")
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()
    try:
        verify_staged_tenant_transport(args.target)
    except (ValueError, RuntimeError, OSError) as exc:
        # No paths, credentials, tokens or original exception text in output.
        print("P0249_Y1_AUTH_TRANSPORT_GATE=DENY", file=sys.stderr)
        raise SystemExit(2) from None
    print("P0249_Y1_AUTH_TRANSPORT_GATE=PASS (synthetic offline, no cloud)")


if __name__ == "__main__":
    main()
