"""Feature7 offline durable dispatch: crash, retries, rights and fencing.

The test context is fabricated and grants no real approval. This is only a
local SQLite stand-in for coordinator-owned Postgres outbox + renderer side
effect idempotency. No paid GPU, Azure, external APIs or media upload.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import json
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'video-engine'/'feature7'))
from review_journal import CurrentReviewContext,ReviewStateError,LocalReviewJournal
from review_dispatch_journal import LocalApprovedEditDispatch

DRAFT='a'*64
CANDIDATE='b'*64
SOURCE='c'*64
OUTPUT='d'*64


def ctx(shop='shop-a',rights=True,role='EDITOR',source=SOURCE):
    return CurrentReviewContext(
      shop_id=shop,campaign_id='campaign-a',reviewer_id='reviewer-a',
      role=role,active_membership=True,
      video_rights_current=rights,media_snapshot_sha256=source)


class Feature7DispatchJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='feature7-dispatch-')
        self.database=Path(self.temp.name)/'review_dispatch.sqlite'
        self.reviews=LocalReviewJournal(self.database)
        self.store=LocalApprovedEditDispatch(self.database)

    def tearDown(self):
        self.store.close()
        self.reviews.close()
        self.temp.cleanup()

    def stage(self):
        review=self.reviews.stage(context=ctx(),
          draft_sha256=DRAFT,candidate_sha256=CANDIDATE,now_ms=900)
        approval=self.reviews.approve(review_id=review['review_id'],
          expected_revision=0,context=ctx(),candidate_sha256=CANDIDATE,
          confirmed_by_human=True,now_ms=950)
        job=self.store.stage_approved(context=ctx(),
          review_id=review['review_id'],approval_id=approval['approval_id'],
          draft_sha256=DRAFT,candidate_sha256=CANDIDATE,
          human_confirmed=True,now_ms=1000)
        return {**job,'review_id':review['review_id'],
          'approval_id':approval['approval_id']}

    def test_normal_lease_ack_prevents_duplicate_consumer(self):
        job=self.stage()
        self.assertFalse(job['approved'])
        lease=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=1000)
        self.assertEqual(lease.idempotency_key,job['idempotency_key'])
        self.assertEqual(lease.attempt,1)
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=1200))
        complete=self.store.finish(context=ctx(),lease=lease,
          result_sha256=OUTPUT,now_ms=1300)
        self.assertEqual(complete['state'],'SUCCEEDED')
        self.assertEqual(self.store.inspect(
          context=ctx(),dispatch_id=job['dispatch_id'])['result_sha256'],OUTPUT)
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=2500))
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=lease,
              result_sha256=OUTPUT,now_ms=1400)


    def test_all_lease_identity_fields_fenced_on_heartbeat_retry_and_ack(self):
        job=self.stage()
        lease=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=2000)
        altered={
          'shop_id':'foreign-shop','campaign_id':'foreign-campaign',
          'draft_sha256':'e'*64,'candidate_sha256':'f'*64,
          'idempotency_key':'f7job_wrong','dispatch_id':'f7d_unknown',
          'fence':'a'*32,'expires_ms':lease.expires_ms+1,
          'attempt':lease.attempt+1
        }
        for key,value in altered.items():
            forged=replace(lease,**{key:value})
            with self.subTest(field=key):
                operations=(
                  lambda:self.store.heartbeat(context=ctx(),lease=forged,
                                               now_ms=1200,lease_ms=1000),
                  lambda:self.store.fail_and_retry(context=ctx(),lease=forged,
                                                    now_ms=1200),
                  lambda:self.store.finish(context=ctx(),lease=forged,
                                           result_sha256=OUTPUT,now_ms=1200))
                for operation in operations:
                    with self.assertRaises(ReviewStateError):
                        operation()
                self.assertEqual(self.store.inspect(
                  context=ctx(),dispatch_id=job['dispatch_id'])['state'],'LEASED')
        self.assertEqual(self.store.finish(context=ctx(),lease=lease,
          result_sha256=OUTPUT,now_ms=1250)['state'],'SUCCEEDED')
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=5000))

    def test_malformed_worker_lease_denied_without_changing_dispatch(self):
        job=self.stage()
        lease=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=2000)
        invalid=(None,{},'not-a-lease',replace(lease,attempt=True),
                 replace(lease,expires_ms='late'),
                 replace(lease,fence=None))
        for forged in invalid:
            with self.subTest(forged=repr(forged)):
                for method in (
                  lambda:self.store.heartbeat(context=ctx(),lease=forged,
                                               now_ms=1200),
                  lambda:self.store.fail_and_retry(context=ctx(),lease=forged,
                                                    now_ms=1200),
                  lambda:self.store.finish(context=ctx(),lease=forged,
                                           result_sha256=OUTPUT,now_ms=1200)):
                    with self.assertRaises(ReviewStateError):
                        method()
        self.assertEqual(self.store.inspect(context=ctx(),
          dispatch_id=job['dispatch_id'])['attempt'],1)
        self.assertEqual(self.store.finish(context=ctx(),lease=lease,
          result_sha256=OUTPUT,now_ms=1300)['state'],'SUCCEEDED')

    def test_revoked_approval_blocks_heartbeat_retry_and_late_ack(self):
        job=self.stage()
        lease=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=2000)
        self.reviews.revoke(review_id=job['review_id'],
          context=ctx(),expected_revision=1)
        for method in (
          lambda:self.store.heartbeat(context=ctx(),lease=lease,now_ms=1200),
          lambda:self.store.fail_and_retry(context=ctx(),lease=lease,now_ms=1200),
          lambda:self.store.finish(context=ctx(),lease=lease,
                                   result_sha256=OUTPUT,now_ms=1200)):
            with self.assertRaises(ReviewStateError):
                method()
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=1300))
        self.assertEqual(self.store.inspect(context=ctx(),
          dispatch_id=job['dispatch_id'])['state'],'REVOKED')
        self.assertIsNone(self.store.reconcile_by_idempotency(
          context=ctx(),idempotency_key=job['idempotency_key'])['result_sha256'])

    def test_crash_then_retry_reopens_with_new_attempt_and_fence(self):
        job=self.stage()
        first=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=1000)
        self.store.close()
        self.store=LocalApprovedEditDispatch(self.database)
        second=self.store.lease_next(context=ctx(),now_ms=2100,lease_ms=1000)
        self.assertEqual(second.idempotency_key,first.idempotency_key)
        self.assertEqual(second.attempt,2)
        self.assertNotEqual(second.fence,first.fence)
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=first,
              result_sha256=OUTPUT,now_ms=2150)
        self.assertEqual(self.store.finish(context=ctx(),lease=second,
          result_sha256=OUTPUT,now_ms=2200)['state'],'SUCCEEDED')
        self.assertEqual(job['idempotency_key'],second.idempotency_key)

    def test_uncertain_ack_reconciles_without_duplicate_submission(self):
        job=self.stage()
        lease=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=1000)
        self.store.finish(context=ctx(),lease=lease,result_sha256=OUTPUT,
          now_ms=1200)
        # Response was lost to the caller. Query, do NOT enqueue again.
        recovered=self.store.reconcile_by_idempotency(context=ctx(),
          idempotency_key=job['idempotency_key'])
        self.assertEqual(recovered['state'],'SUCCEEDED')
        self.assertEqual(recovered['result_sha256'],OUTPUT)
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=5000))
        with self.assertRaises(ReviewStateError):
            self.store.reconcile_by_idempotency(
                context=ctx(shop='foreign'),
                idempotency_key=job['idempotency_key'])
        with self.assertRaises(ReviewStateError):
            self.store.reconcile_by_idempotency(
                context=ctx(source='d'*64),
                idempotency_key=job['idempotency_key'])

    def test_heartbeat_extends_only_current_lease(self):
        self.stage()
        first=self.store.lease_next(context=ctx(),now_ms=1000,lease_ms=1000)
        extended=self.store.heartbeat(context=ctx(),lease=first,
          now_ms=1500,lease_ms=2000)
        self.assertEqual(extended.expires_ms,3500)
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=first,
              result_sha256=OUTPUT,now_ms=1700)
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=2500))
        self.assertEqual(self.store.finish(context=ctx(),lease=extended,
          result_sha256=OUTPUT,now_ms=3000)['state'],'SUCCEEDED')

    def test_denied_foreign_revoked_viewer_and_unknown_source(self):
        job=self.stage()
        for wrong in (ctx(shop='foreign'),ctx(rights=False),
                      ctx(role='VIEWER'),ctx(source='f'*64)):
            with self.subTest(incorrect_context=wrong):
                with self.assertRaises(ReviewStateError):
                    self.store.inspect(context=wrong,dispatch_id=job['dispatch_id'])
                self.assertIsNone(
                    self.store.lease_next(context=wrong,now_ms=1200)
                    if wrong.role!='VIEWER' and wrong.video_rights_current
                    else None)
        with self.assertRaises(ReviewStateError):
            self.store.stage_approved(context=ctx(role='VIEWER'),
              review_id='viewer_review',approval_id='viewer_approve',
              draft_sha256=DRAFT,candidate_sha256=CANDIDATE,
              human_confirmed=True,now_ms=1000)
        with self.assertRaises(ReviewStateError):
            self.store.stage_approved(context=ctx(),
              review_id='no_human',approval_id='approval_no_human',
              draft_sha256=DRAFT,candidate_sha256=CANDIDATE,
              human_confirmed=False,now_ms=1000)

    def test_staging_duplicate_ids_rejected_transactionally(self):
        first=self.stage()
        with self.assertRaises(ReviewStateError):
            self.store.stage_approved(context=ctx(),
              review_id=first['review_id'],approval_id=first['approval_id'],
              draft_sha256=DRAFT,candidate_sha256=CANDIDATE,
              human_confirmed=True,now_ms=1000)
        for changed in [
          {'approval_id':'wrong_approval'},
          {'draft_sha256':'e'*64},
          {'candidate_sha256':'f'*64}
        ]:
            with self.subTest(changed=changed):
                request={'context':ctx(),'review_id':first['review_id'],
                  'approval_id':first['approval_id'],
                  'draft_sha256':DRAFT,'candidate_sha256':CANDIDATE,
                  'human_confirmed':True,'now_ms':1000}
                request.update(changed)
                with self.assertRaises(ReviewStateError):
                    self.store.stage_approved(**request)
        self.assertEqual(self.store.inspect(
            context=ctx(),dispatch_id=first['dispatch_id'])['state'],'READY')

    def test_unapproved_review_cannot_be_queued_even_if_human_flag_true(self):
        pending=self.reviews.stage(context=ctx(),draft_sha256=DRAFT,
          candidate_sha256=CANDIDATE,now_ms=900)
        with self.assertRaises(ReviewStateError):
            self.store.stage_approved(context=ctx(),
              review_id=pending['review_id'],approval_id='f7a_fake123',
              draft_sha256=DRAFT,candidate_sha256=CANDIDATE,
              human_confirmed=True,now_ms=1000)

    def test_retry_exponential_external_and_poison_after_limit(self):
        job=self.stage()
        for attempt in range(1,5):
            start=2000+(attempt-1)*2000
            lease=self.store.lease_next(context=ctx(),now_ms=start,lease_ms=1000)
            self.assertIsNotNone(lease)
            self.assertEqual(lease.attempt,attempt)
            outcome=self.store.fail_and_retry(context=ctx(),lease=lease,
              now_ms=start+100,retry_delay_ms=1000)
            self.assertEqual(outcome['state'],'DEAD' if attempt==4 else 'READY')
            self.assertIsNone(self.store.lease_next(
              context=ctx(),now_ms=start+200))
        self.assertEqual(self.store.inspect(
          context=ctx(),dispatch_id=job['dispatch_id'])['state'],'DEAD')
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=99999))

    def test_persisted_approval_revoked_after_queue_cannot_render(self):
        job=self.stage()
        lease=self.store.lease_next(context=ctx(),now_ms=1100,lease_ms=1000)
        self.reviews.revoke(review_id=job['review_id'],
          context=ctx(),expected_revision=1)
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=lease,
              result_sha256=OUTPUT,now_ms=1200)
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=1200))
        self.assertEqual(self.store.inspect(context=ctx(),
          dispatch_id=job['dispatch_id'])['state'],'REVOKED')

    def test_expired_approval_rejects_queued_render_before_start(self):
        job=self.stage()
        self.assertIsNone(self.store.lease_next(
          context=ctx(),now_ms=950+10*60*1000+1))
        self.assertEqual(self.store.inspect(context=ctx(),
          dispatch_id=job['dispatch_id'])['state'],'REVOKED')

    def test_revoking_active_lease_fences_worker(self):
        job=self.stage()
        lease=self.store.lease_next(context=ctx(),now_ms=1100)
        self.assertEqual(self.store.revoke(context=ctx(),
          dispatch_id=job['dispatch_id'])['state'],'REVOKED')
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=lease,
              result_sha256=OUTPUT,now_ms=1150)
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=90000))

    def test_two_connections_compete_one_claim(self):
        self.stage()
        self.store.close()
        self.store=LocalApprovedEditDispatch(self.database)
        def try_claim(_):
            other=LocalApprovedEditDispatch(self.database)
            try:
                return other.lease_next(context=ctx(),now_ms=1500)
            finally:
                other.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            leases=list(pool.map(try_claim,[0,1]))
        self.assertEqual(sum(lease is not None for lease in leases),1)

    def test_worker_crash_on_final_attempt_becomes_dead_not_stranded(self):
        job=self.stage()
        for attempt in range(1,5):
            start=1000+(attempt-1)*2000
            lease=self.store.lease_next(context=ctx(),now_ms=start,lease_ms=1000)
            self.assertEqual(lease.attempt,attempt)
            # Let each process die without ack, then reclaim next lease.
        self.assertIsNone(self.store.lease_next(context=ctx(),now_ms=9000))
        row=self.store.inspect(context=ctx(),dispatch_id=job['dispatch_id'])
        self.assertEqual(row['state'],'DEAD')
        self.assertEqual(row['attempt'],4)

    def test_invalid_lease_bounds_and_expired_completion_rejected(self):
        self.stage()
        for invalid in (0,100000,True,1.5):
            with self.subTest(lease=invalid):
                with self.assertRaises(ReviewStateError):
                    self.store.lease_next(context=ctx(),now_ms=1000,lease_ms=invalid)
        lease=self.store.lease_next(context=ctx(),now_ms=1000,lease_ms=1000)
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=lease,
              result_sha256=OUTPUT,now_ms=2000)



    @unittest.skipUnless(hasattr(signal, 'SIGKILL'),
                         'Real SIGKILL requires a POSIX CPU runner')
    def test_real_worker_sigkill_releases_expired_lease_with_new_fence(self):
        """The killed worker never ACKs. Reclaim only after expiry with new fence."""
        job=self.stage()
        script="""
import json,os,signal,sys
from dataclasses import asdict
sys.path.insert(0,sys.argv[2])
from review_journal import CurrentReviewContext
from review_dispatch_journal import LocalApprovedEditDispatch
store=LocalApprovedEditDispatch(sys.argv[1])
current=CurrentReviewContext('shop-a','campaign-a','reviewer-a',
  'EDITOR',True,True,'c'*64)
lease=store.lease_next(context=current,now_ms=1100,lease_ms=1000)
assert lease is not None
print(json.dumps(asdict(lease)),flush=True)
os.kill(os.getpid(),signal.SIGKILL)
"""
        proc=subprocess.run(
            [sys.executable,'-c',script,str(self.database),
             str(ROOT/'video-engine'/'feature7')],
            capture_output=True,text=True,timeout=15)
        self.assertEqual(proc.returncode,-signal.SIGKILL,proc.stderr)
        from review_dispatch_journal import DispatchLease
        first=DispatchLease(**json.loads(proc.stdout.strip()))
        self.assertEqual(first.attempt,1)
        self.assertEqual(first.idempotency_key,job['idempotency_key'])
        self.assertIsNone(self.store.lease_next(
            context=ctx(),now_ms=1500,lease_ms=1000))
        # The worker process is dead, but SQLite WAL receipt survives.
        self.store.close()
        self.store=LocalApprovedEditDispatch(self.database)
        second=self.store.lease_next(
            context=ctx(),now_ms=2100,lease_ms=1000)
        self.assertIsNotNone(second)
        self.assertEqual(second.attempt,2)
        self.assertNotEqual(first.fence,second.fence)
        self.assertEqual(first.idempotency_key,second.idempotency_key)
        with self.assertRaises(ReviewStateError):
            self.store.finish(context=ctx(),lease=first,
              result_sha256=OUTPUT,now_ms=2150)
        self.assertEqual(self.store.finish(
            context=ctx(),lease=second,
            result_sha256=OUTPUT,now_ms=2200)['state'],'SUCCEEDED')
        self.assertIsNone(self.store.lease_next(
            context=ctx(),now_ms=5000,lease_ms=1000))

if __name__=='__main__':
    unittest.main()
