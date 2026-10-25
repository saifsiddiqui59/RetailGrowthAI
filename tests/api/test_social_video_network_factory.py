"""Offline guarded provider transport composition; never calls real Meta/Google."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
import social_video_network_factory as net_factory
from social_video_network_factory import build_guarded_video_network_sender
from social_video_worker_factory import _REQUIRED_SWITCHES, VideoWorkerDisabled
from social_media_transport import (
    ProviderRequest as TransportProviderRequest, MediaNetworkTransport,
)
from social_dispatch import ProviderFailure

JOB="62000000-0000-4000-8000-000000000001"
LEASE="92000000-0000-4000-8000-000000000001"
ALL={flag:"true" for flag in _REQUIRED_SWITCHES}
ALL["RETAIL_PART2_VIDEO_NETWORK_TRANSPORT_ENABLED"]="true"


class Response:
    def __init__(self,url,status=200,body=b'{"status_code":"FINISHED"}'):
        self.url,self.status,self.body=url,status,body
        self.headers={}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,n):return self.body[:n]


def setup(monkeypatch):
    recorded=[]
    def builder(config,**kw):
        recorded.append((config,kw))
        return {"reviewed_sender_created":True,"provider_transport":kw["provider_transport"]}
    monkeypatch.setattr(net_factory,"build_guarded_video_sender",builder)
    return recorded


def test_no_implicit_network_provider_or_azure_registration(monkeypatch):
    made=setup(monkeypatch)
    called=[]
    with pytest.raises(VideoWorkerDisabled,match="remains disabled"):
        build_guarded_video_network_sender(
            dict(ALL),job_id=JOB,claim_token=LEASE,
            provider_opener=lambda r,timeout:called.append(r))
    assert made==[] and called==[]


@pytest.mark.parametrize("missing",list(_REQUIRED_SWITCHES)+[
    "RETAIL_PART2_VIDEO_NETWORK_TRANSPORT_ENABLED"])
def test_all_seven_switches_must_be_explicitly_true(monkeypatch,missing):
    recorded=setup(monkeypatch)
    config=dict(ALL)
    config.pop(missing)
    with pytest.raises(VideoWorkerDisabled,match="remains disabled"):
        build_guarded_video_network_sender(
            config,job_id=JOB,claim_token=LEASE,enabled=True)
    assert recorded==[]


@pytest.mark.parametrize("bad",[None, {},[],True, "enabled", lambda : "bad"])
def test_network_flag_cannot_be_truthy_or_substituted(monkeypatch,bad):
    recorded=setup(monkeypatch)
    config=dict(ALL)
    config["RETAIL_PART2_VIDEO_NETWORK_TRANSPORT_ENABLED"]=bad
    with pytest.raises(VideoWorkerDisabled,match="remains disabled"):
        build_guarded_video_network_sender(
            config,job_id=JOB,claim_token=LEASE,enabled=True)
    assert recorded==[]


def test_composes_exact_scoped_sender_and_zero_network_until_called(monkeypatch):
    recorded=setup(monkeypatch)
    network_calls=[]
    def opener(req,timeout):
        network_calls.append(req)
        return Response(req.full_url)
    result=build_guarded_video_network_sender(
        dict(ALL),job_id=JOB,claim_token=LEASE,
        provider_opener=opener,enabled=True,
        storage_transport="fake-service-postgrest",probe="fake-ffprobe",
        clock="fake-clock")
    assert result["reviewed_sender_created"] is True
    assert len(recorded)==1 and network_calls==[]
    config,kw=recorded[0]
    assert kw["job_id"]==JOB and kw["claim_token"]==LEASE
    assert kw["storage_transport"]=="fake-service-postgrest"
    assert kw["probe"]=="fake-ffprobe" and kw["clock"]=="fake-clock"
    assert isinstance(kw["provider_transport"],MediaNetworkTransport)
    # This only simulates a provider GET via our strict injected opener.
    request=TransportProviderRequest(
        "GET","https://graph.facebook.com/v26.0/987654321?fields=status_code",
        {"Authorization":"Bearer fake-token"}, {})
    assert kw["provider_transport"](request)[1]=={"status_code":"FINISHED"}
    assert len(network_calls)==1 and network_calls[0].get_method()=="GET"


def test_provider_transport_stays_host_and_method_allowlisted(monkeypatch):
    recorded=setup(monkeypatch)
    network_calls=[]
    composed=build_guarded_video_network_sender(
        dict(ALL),job_id=JOB,claim_token=LEASE,enabled=True,
        provider_opener=lambda req,timeout:network_calls.append(req))
    transport=composed["provider_transport"]
    with pytest.raises(ProviderFailure,match="UNAPPROVED_MEDIA_ENDPOINT"):
        transport(TransportProviderRequest(
            "POST","https://evil.example/upload",{"Authorization":"Bearer x"},{}))
    with pytest.raises(ProviderFailure,match="UNAPPROVED_MEDIA_ENDPOINT"):
        transport(TransportProviderRequest(
            "POST","https://graph.facebook.com/v26.0/987654321?fields=status_code",
            {"Authorization":"Bearer x"},{}))
    assert network_calls==[] and len(recorded)==1


def test_malformed_opener_denied_without_worker_construction(monkeypatch):
    recorded=setup(monkeypatch)
    with pytest.raises(VideoWorkerDisabled,match="opener"):
        build_guarded_video_network_sender(
            dict(ALL),job_id=JOB,claim_token=LEASE,
            provider_opener="this-is-not-a-callable",enabled=True)
    assert recorded==[]
