"""Offline PNG upload boundary: tenant path, image decode, lease and immutability."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from private_poster_media import PrivatePosterMedia, validate_output_png
from tenant_store import StorageUnavailable

SID, PID, LEASE = (str(uuid4()) for _ in range(3))


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False


def new_png(tmp_path, size=(1080, 1080), *, mode="RGB"):
    path = tmp_path / "output.png"
    Image.new(mode, size, "#B08475").save(path)
    return path


def uploader(calls):
    def transport(req, timeout):
        calls.append((req, timeout))
        return Response()
    return PrivatePosterMedia("https://retail.supabase.co", "sb_secret_poster_ci_only", transport)


@pytest.mark.parametrize("preset,size", [("square", (1080, 1080)), ("portrait", (1080, 1350))])
def test_authorized_upload_key_is_private_claim_scoped(tmp_path, preset, size):
    calls = []
    key = uploader(calls).upload_png(SID, PID, LEASE, new_png(tmp_path, size), format_name=preset)
    assert key == f"{SID}/posters/{PID}/{LEASE}.png"
    request, timeout = calls[0]
    assert request.get_method() == "POST" and timeout == 60
    assert request.full_url.endswith("/storage/v1/object/retailgrowth-media/" + key)
    assert request.get_header("Apikey") == "sb_secret_poster_ci_only"
    assert request.get_header("Authorization") is None
    assert request.get_header("X-upsert") == "false"
    assert request.get_header("Content-type") == "image/png"
    assert request.data.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("field", ["shop", "poster", "lease"])
def test_invalid_id_rejected_before_any_upload(tmp_path, field):
    calls = []
    ids = dict(shop=SID, poster=PID, lease=LEASE)
    ids[field] = "../foreign-tenant"
    with pytest.raises(ValueError):
        uploader(calls).upload_png(ids["shop"], ids["poster"], ids["lease"],
                                   new_png(tmp_path), format_name="square")
    assert calls == []


def test_incorrect_aspect_ratio_does_not_upload(tmp_path):
    calls = []
    with pytest.raises(StorageUnavailable, match="approved preset"):
        uploader(calls).upload_png(SID, PID, LEASE, new_png(tmp_path), format_name="portrait")
    assert not calls


def test_false_png_or_truncated_png_cannot_upload(tmp_path):
    calls = []
    png = new_png(tmp_path)
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"garbage" * 100)
    with pytest.raises(StorageUnavailable):
        uploader(calls).upload_png(SID, PID, LEASE, png, format_name="square")
    png = new_png(tmp_path)
    png.write_bytes(png.read_bytes()[:-60])
    with pytest.raises(StorageUnavailable):
        uploader(calls).upload_png(SID, PID, LEASE, png, format_name="square")
    assert not calls


def test_rgba_rejected_as_renderer_output_must_be_rgb(tmp_path):
    with pytest.raises(StorageUnavailable, match="approved preset"):
        validate_output_png(new_png(tmp_path, mode="RGBA"), "square")


def test_symbolic_link_rejected_before_upload(tmp_path):
    original = new_png(tmp_path)
    alias = tmp_path / "linked.png"
    alias.symlink_to(original)
    calls = []
    with pytest.raises(StorageUnavailable, match="regular file"):
        uploader(calls).upload_png(SID, PID, LEASE, alias, format_name="square")
    assert not calls


def test_collision_is_never_counted_as_success(tmp_path):
    def conflict(req, timeout):
        raise HTTPError(req.full_url, 409, "exists", {}, io.BytesIO())
    with pytest.raises(StorageUnavailable, match="collision"):
        PrivatePosterMedia("https://retail.supabase.co", "sb_secret_ci_only", conflict).upload_png(
            SID, PID, LEASE, new_png(tmp_path), format_name="square")


def test_network_failure_never_returns_success_key(tmp_path):
    def failed(req, timeout):
        raise URLError("unreachable")
    with pytest.raises(StorageUnavailable, match="unavailable"):
        PrivatePosterMedia("https://retail.supabase.co", "sb_secret_ci_only", failed).upload_png(
            SID, PID, LEASE, new_png(tmp_path), format_name="square")


def test_missing_file_and_unsupported_format_rejected(tmp_path):
    calls = []
    with pytest.raises(StorageUnavailable):
        uploader(calls).upload_png(SID, PID, LEASE, tmp_path / "missing.png", format_name="square")
    with pytest.raises(ValueError):
        uploader(calls).upload_png(SID, PID, LEASE, new_png(tmp_path), format_name="story")
    assert calls == []


def test_over_budget_output_rejected_without_network(tmp_path):
    path = tmp_path / "large.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * (12 * 1024 * 1024 + 1))
    calls = []
    with pytest.raises(StorageUnavailable, match="size out of bounds"):
        uploader(calls).upload_png(SID, PID, LEASE, path, format_name="square")
    assert not calls
