"""Offline regression: social service-role calls must not follow redirects."""
import sys
from pathlib import Path
from urllib.request import Request

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
import social_jobs_repository as jobs

ORIGIN = "https://retail-test.supabase.co"
SECRET = "sb_secret_" + "x" * 40


class Response:
    def __init__(self, location):
        self.location = location
        self.read_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.location

    def read(self, limit):
        self.read_calls += 1
        return b"{}"


def test_foreign_redirect_cannot_receive_or_appear_as_authoring_result():
    seen = []
    response = Response("https://attacker.example/steal")
    def transport(request, timeout):
        seen.append((request, timeout))
        return response

    repository = jobs.SocialAuthoringRepository(ORIGIN, SECRET, transport=transport)
    request = Request(ORIGIN + "/rest/v1/rpc/p2_create_social_draft",
                      headers=repository.headers, method="POST", data=b"{}")
    with pytest.raises(jobs.StorageUnavailable, match="unexpected social backend redirect"):
        repository._send(request)
    assert response.read_calls == 0
    assert len(seen) == 1
    assert seen[0][0].get_header("Apikey") == SECRET


def test_default_authoring_client_is_explicitly_redirect_blocked(monkeypatch):
    installed = []
    class Opener:
        def open(self, request, timeout):
            raise AssertionError("no network in unit test")
    def fake_opener(handler):
        installed.append(handler)
        return Opener()
    monkeypatch.setattr(jobs, "build_opener", fake_opener)
    repository = jobs.SocialAuthoringRepository(ORIGIN, SECRET)
    assert installed and isinstance(installed[0], jobs._NoRedirect)
    assert installed[0].redirect_request(None, None, 302, "redirect",
                                          {}, "https://attacker.example") is None
    assert repository.transport.__self__.__class__ is Opener


@pytest.mark.parametrize("origin", [
    "https://retail-test.supabase.co:8443",
    "https://retail-test.supabase.co@attacker.example",
    "http://retail-test.supabase.co",
    "https://retail-test.supabase.co/v1",
])
def test_authoring_origin_cannot_route_to_unreviewed_host_or_port(origin):
    with pytest.raises(ValueError):
        jobs.SocialAuthoringRepository(origin, SECRET, transport=lambda *_: None)
