"""Offline due-social queue adapter tests, no hosted Azure or provider calls."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_due_queue import SOCIAL_QUEUE, AzureSocialQueue, SocialDueStore, enqueue_due_jobs
from tenant_store import StorageUnavailable

ONE="13000000-0000-4000-8000-000000000001"
TWO="13000000-0000-4000-8000-000000000002"


class Response:
    def __init__(self, url, rows):
        self.url=url
        self.rows=rows
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,amount):return json.dumps(self.rows).encode("utf-8")

class Transport:
    def __init__(self,rows):self.rows=rows;self.requests=[]
    def __call__(self,req,timeout):
        self.requests.append((req,timeout))
        return Response(req.full_url,self.rows)


class Queue:
    def __init__(self,fail=False):self.ids=[];self.fail=fail
    def enqueue(self,jid):
        if self.fail:raise RuntimeError("queue unavailable")
        self.ids.append(jid)


def store(rows):
    return SocialDueStore("https://tenant.supabase.co",
                          "sb_secret_"+ "x"*32,transport=Transport(rows))

def test_due_ids_fixed_service_only_post_and_no_tokens_in_queue():
    fake=Transport([{"job_id":ONE},{"job_id":TWO}])
    s=SocialDueStore("https://tenant.supabase.co",
          "sb_secret_" + "x"*32,transport=fake)
    assert s.due(5)==[ONE,TWO]
    req,timeout=fake.requests[0]
    assert req.full_url=="https://tenant.supabase.co/rest/v1/rpc/p2_due_social_job_ids"
    assert req.get_method()=="POST"
    assert json.loads(req.data)=={"p_limit":5}
    assert req.headers["Apikey"].startswith("sb_secret_")
    assert timeout==10
    q=Queue()
    assert enqueue_due_jobs(s,q)==2
    assert q.ids==[ONE,TWO]
    assert all(len(j)==36 for j in q.ids)

def test_transport_rejects_bad_origin_ids_and_duplication():
    for origin in [
      "http://tenant.supabase.co","https://attacker@tenant.supabase.co",
      "https://tenant.supabase.co/path",
      "https://tenant.supabase.co/?x=1",
      "https://tenant.supabase.co:8443",
      "https://tenant.supabase.co:invalid",
      "https://tenant.supabase.co\r\nX-Fake:yes",
      "https://tenant.supabase.co/#secret",
    ]:
        with pytest.raises(ValueError): SocialDueStore(origin,"sb_secret_x")
    with pytest.raises(StorageUnavailable):
        store([{"job_id":"../invalid"}]).due()
    with pytest.raises(StorageUnavailable):
        store([{"job_id":ONE},{"job_id":ONE}]).due()
    with pytest.raises(StorageUnavailable):
        store([{"job_id":ONE,"secret":"access_token"}]).due()
    with pytest.raises(ValueError):
        store([]).due(0)

def test_wrong_shape_or_large_batch_cannot_enqueue_partial_messages():
    class FakeStore:
        def due(self,limit):return [ONE,"../other"]
    q=Queue()
    with pytest.raises(Exception):
        enqueue_due_jobs(FakeStore(),q)
    assert q.ids==[]
    class DupStore:
        def due(self,limit):return [ONE,ONE]
    with pytest.raises(StorageUnavailable):
        enqueue_due_jobs(DupStore(),q)
    assert q.ids==[]

def test_queue_uuid_only_and_no_implicit_provision():
    class Client:
        def __init__(self):self.sent=[]
        def send_message(self,value):self.sent.append(value)
        def create_queue(self):raise AssertionError("must never provision")
    client=Client()
    q=AzureSocialQueue("StorageEndpoint=mock",client=client)
    q.enqueue(ONE)
    assert client.sent==[ONE]
    assert SOCIAL_QUEUE=="retail-social-publish"
    with pytest.raises(Exception):q.enqueue("not-a-uuid")
    assert client.sent==[ONE]

def test_send_error_is_not_acknowledged_or_relabelled_success():
    with pytest.raises(RuntimeError,match="queue unavailable"):
        enqueue_due_jobs(store([{"job_id":ONE}]),Queue(fail=True))
