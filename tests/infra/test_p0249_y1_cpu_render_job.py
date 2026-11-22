"""Source-only contract tests: new CPU job never double ACKs private render work."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ops/p0249-y1-cutover/cpu_render_job.py"
spec = importlib.util.spec_from_file_location("p0249_cpu_job", SOURCE)
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)

GOOD_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class FakeQueue:
    def __init__(self, items):
        self.items = items
        self.acks = []
        self.reads = []

    def receive_messages(self, **kw):
        self.reads.append(kw)
        return iter(self.items)

    def delete_message(self, mid, receipt):
        self.acks.append((mid, receipt))


def msg(content=GOOD_ID):
    return SimpleNamespace(content=content, id="private-mid", pop_receipt="private-receipt")


class Y1CpuQueueSafety(unittest.TestCase):
    def test_normal_success_acks_exact_delivered_receipt(self):
        for status in sorted(job.SUCCESS):
            with self.subTest(status=status):
                queue = FakeQueue([msg()])
                calls = []
                def render(identifier, admin, media):
                    calls.append((identifier, admin, media))
                    return status
                result = job.process_one(queue, "admin", "media", render)
                self.assertEqual(result, status)
                self.assertEqual(calls, [(GOOD_ID, "admin", "media")])
                self.assertEqual(queue.acks, [("private-mid", "private-receipt")])
                self.assertEqual(queue.reads, [
                    {"messages_per_page": 1, "visibility_timeout": 1500}])

    def test_no_message_never_renders_or_acks(self):
        queue = FakeQueue([])
        self.assertEqual(job.process_one(queue, 1, 2,
                         lambda *_: self.fail("rendered empty queue")), "EMPTY")
        self.assertEqual(queue.acks, [])

    def test_invalid_payload_or_unknown_commit_never_acks(self):
        for malformed in ("", "unknown", "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
                          "not-a-uuid", "../../other", "0"*36):
            q = FakeQueue([msg(malformed)])
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                job.process_one(q, None, None, lambda *_: "SUCCEEDED")
            self.assertEqual(q.acks, [])
        q = FakeQueue([msg()])
        with self.assertRaisesRegex(RuntimeError, "not committed"):
            job.process_one(q, None, None, lambda *_: "RETRYABLE")
        self.assertEqual(q.acks, [])

    def test_render_exception_never_acknowledges(self):
        q = FakeQueue([msg()])
        def fails(*_):
            raise RuntimeError("simulated DB lease conflict")
        with self.assertRaises(RuntimeError):
            job.process_one(q, None, None, fails)
        self.assertEqual(q.acks, [])

    def test_over_retry_budget_enters_original_deduplicating_poison_queue(self):
        class Admin:
            def render_status(self, job_id):
                self.last = job_id
                return "QUEUED"
        class Poison:
            def __init__(self):
                self.messages = []
            def send_message(self, payload):
                self.messages.append(payload)
                return SimpleNamespace(id="confirmed-poison-ack")
        pending=msg()
        pending.dequeue_count=4
        queue=FakeQueue([pending])
        admin=Admin()
        poison=Poison()
        result=job.process_one(queue,admin,None,
                   lambda *_: self.fail("Cannot render over-budget queue item"),poison)
        self.assertEqual(result,"POISONED")
        self.assertEqual(admin.last,GOOD_ID)
        self.assertEqual(poison.messages,[GOOD_ID])
        self.assertEqual(queue.acks,[("private-mid","private-receipt")])

    def test_poison_failure_or_uncertain_ack_never_deletes_original(self):
        class Admin:
            def render_status(self,_): return "QUEUED"
        class Poison:
            def __init__(self, ack): self.ack=ack
            def send_message(self,_):
                if self.ack is None: raise RuntimeError("transport interrupted")
                return SimpleNamespace(id=self.ack)
        for ack in (None,""):
            pending=msg()
            pending.dequeue_count=4
            queue=FakeQueue([pending])
            with self.subTest(ack=ack),self.assertRaises(RuntimeError):
                job.process_one(queue,Admin(),None,
                       lambda *_:"SUCCEEDED",Poison(ack))
            self.assertEqual(queue.acks,[])

    def test_finalized_job_dequeues_without_duplicate_poison_or_bill(self):
        class Admin:
            def render_status(self,_): return "SUCCEEDED"
        pending=msg()
        pending.dequeue_count=4
        queue=FakeQueue([pending])
        self.assertEqual(job.process_one(queue,Admin(),None,
             lambda *_: self.fail("Replayed a final render")),
             "ALREADY_FINAL")
        self.assertEqual(queue.acks,[("private-mid","private-receipt")])

    def test_invalid_attempt_counter_never_processes_or_acks(self):
        for count in (-1,0,1.5,"3",True,1001):
            pending=msg()
            pending.dequeue_count=count
            queue=FakeQueue([pending])
            with self.subTest(count=count), self.assertRaises(RuntimeError):
                job.process_one(queue,None,None,
                                lambda *_:self.fail("bad count rendered"))
            self.assertEqual(queue.acks,[])

    def test_explicit_dev_handoff_and_longer_than_780s_budget_required(self):
        env = {
            "RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED": "VERIFIED_FLEX_RENDER_CONSUMER_DISABLED",
            "RGAI_CPU_RENDER_HOSTING": "azure-container-apps-job",
            "RGAI_CPU_RENDER_RG": "rg-retailgrowth-dev",
            "RETAIL_SUPABASE_URL": job.EXPECTED_SUPABASE,
            "RGAI_CPU_RENDER_QUEUE_NAME": job.QUEUE,
            "RGAI_CPU_RENDER_REPLICA_TIMEOUT_SECONDS": "1800",
            "RETAIL_STORAGE": "server-secret-" + "a"*50,
            "RETAIL_SUPABASE_SERVICE_ROLE_KEY": "server-secret-" + "b"*50,
        }
        job.preflight(env)
        self.assertEqual(job.CONTAINER_REPLICA_TIMEOUT_SECONDS, 1800)
        self.assertGreater(job.CONTAINER_REPLICA_TIMEOUT_SECONDS, 780)
        self.assertEqual(job.VISIBILITY_SECONDS, 1500)
        self.assertGreater(job.VISIBILITY_SECONDS, 780)
        for name, wrong in (
            ("RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED", "false"),
            ("RGAI_CPU_RENDER_HOSTING", "classic-y1"),
            ("RGAI_CPU_RENDER_RG", "another-project"),
            ("RETAIL_SUPABASE_URL", "https://foreign.example"),
            ("RGAI_CPU_RENDER_QUEUE_NAME", "external"),
            ("RGAI_CPU_RENDER_REPLICA_TIMEOUT_SECONDS", "600"),
            ("RETAIL_STORAGE", ""),
            ("RETAIL_SUPABASE_SERVICE_ROLE_KEY", ""),
        ):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                job.preflight({**env, name:wrong})
        for key in env:
            with self.subTest(missing=key), self.assertRaises(RuntimeError):
                job.preflight({k:v for k,v in env.items() if k!=key})

    def test_exact_uploaded_post_bytes_verified_before_returning_private_key(self):
        import hashlib
        from urllib.request import Request

        class Storage:
            origin = "https://dev-storage.example"
            body = b"mp4-synthetic-fixture-" * 150
            def __init__(self):
                self.posts = []
                self.checks = []
                self.transport = self.send
                self.calls = []
            def send(self, req, timeout):
                self.posts.append((req.get_method(), req.full_url,
                                   req.data, timeout))
                return SimpleNamespace(status=200)
            def download(self, *args, **kwargs):
                self.calls.append(("download", args))
                return "downloaded"
            def upload(self, shop_id, job_id, media_file, *, lease_token):
                self.calls.append(("upload", lease_token))
                req = Request(
                    self.origin + "/storage/v1/object/retailgrowth-media/"
                                + shop_id + "/renders/" + job_id + ".mp4",
                    data=self.body, method="POST")
                self.transport(req, timeout=60)
                return shop_id + "/renders/" + job_id + ".mp4"
            def verify_uploaded_mp4(self, shop_id, key, expected_sha256):
                self.checks.append((shop_id, key, expected_sha256))
                return True

        storage = Storage()
        wrapper = job.VerifiedPrivateMedia(storage)
        self.assertEqual(wrapper.download("shop", "private", "/tmp/mock"),
                         "downloaded")
        key = wrapper.upload("shop", GOOD_ID, "/not-opened",
                             lease_token="fenced")
        self.assertEqual(storage.transport, storage.send)
        self.assertEqual(storage.calls[-1], ("upload", "fenced"))
        self.assertEqual(storage.posts[0][0], "POST")
        self.assertEqual(storage.posts[0][2], storage.body)
        self.assertEqual(storage.checks, [
            ("shop", key, hashlib.sha256(storage.body).hexdigest())])

    def test_private_cpu_upload_missing_remote_confirmation_blocks_success(self):
        from urllib.request import Request

        class Storage:
            origin = "https://dev-storage.example"
            def __init__(self, mode):
                self.mode = mode
                self.transport = self.send
                self.checks = 0
                self.posts = 0
            def send(self, req, timeout):
                self.posts += 1
                return SimpleNamespace(status=200)
            def upload(self, shop_id, job_id, media_file, *, lease_token):
                if self.mode != "no-post":
                    endpoint = (
                        self.origin if self.mode != "foreign" else
                        "https://foreign-storage.example")
                    request = Request(
                        endpoint + "/storage/v1/object/retailgrowth-media/"
                                   + shop_id + "/renders/" + job_id + ".mp4",
                        data=b"synthetic-video" * 200, method="POST")
                    self.transport(request, timeout=60)
                    if self.mode == "duplicate":
                        self.transport(request, timeout=60)
                return "shop/renders/private.mp4"
            def verify_uploaded_mp4(self, *args):
                self.checks += 1
                return self.mode != "readback-failed"

        for mode, text in (
            ("no-post", "No actual private media"),
            ("foreign", "Unsafe or duplicate"),
            ("duplicate", "Unsafe or duplicate"),
            ("readback-failed", "Private video readback failed"),
        ):
            with self.subTest(mode=mode):
                storage = Storage(mode)
                old_transport = storage.transport
                with self.assertRaisesRegex(RuntimeError, text):
                    job.VerifiedPrivateMedia(storage).upload(
                        "shop", GOOD_ID, "/not-opened", lease_token=None)
                self.assertEqual(storage.transport, old_transport)
                self.assertEqual(storage.checks,
                                 1 if mode == "readback-failed" else 0)

    def test_source_has_no_loop_or_resource_provisioning(self):
        code=SOURCE.read_text()
        self.assertNotIn("create_queue", code)
        self.assertNotIn("queue.send_message(", code)
        self.assertIn("poison.send_message(jid)", code)
        self.assertIn('POISON_QUEUE = "retail-reel-render-poison"', code)
        self.assertNotIn("while True", code)
        self.assertNotIn("az containerapp", code)
        self.assertNotIn("az functionapp stop", code)
        self.assertNotIn("print(secret", code)
        self.assertNotIn("print(job_id", code)


if __name__ == "__main__":
    unittest.main()
