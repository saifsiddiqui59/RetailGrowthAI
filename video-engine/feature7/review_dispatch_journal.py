"""Feature7 LOCAL crash-recoverable human-approved edit dispatch prototype.

Only a single-machine SQLite source/test implementation. All identities,
membership/rights snapshots, SHA values and approvals must come from a
trusted JWT/RLS server transaction before this is called. Unlike the older
one-shot LocalReviewJournal.claim_for_feature4, this module does not mark
a job consumed before a renderer confirms the result. An expired LEASE may
be reclaimed by a different worker with a NEW fencing token.

This is AT-LEAST-ONCE delivery with a stable idempotency key, not exactly-once
external rendering. Feature4 must atomically honor dispatch_id + attempt fence
when committing side effects, or duplicate output is possible after a crash.
No footage, client JWT, HMAC secrets or transcript bytes are stored.
"""
from __future__ import annotations

from dataclasses import dataclass
import secrets
import sqlite3
import time
from pathlib import Path

from review_journal import CurrentReviewContext, ReviewStateError, _clock, _digest, _identifier

LEASE_MS = 90 * 1000
MAX_ATTEMPTS = 4
ID_PREFIX = "f7d_"


@dataclass(frozen=True)
class DispatchLease:
    dispatch_id: str
    idempotency_key: str
    attempt: int
    fence: str
    expires_ms: int
    shop_id: str
    campaign_id: str
    draft_sha256: str
    candidate_sha256: str


class LocalApprovedEditDispatch:
    """Single-process SQLite store with WAL and revision-safe job leases."""

    def __init__(self, filename: str | Path):
        self.db = sqlite3.connect(str(filename), timeout=15, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=15000")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS f7_approved_edit_dispatch (
            dispatch_id TEXT PRIMARY KEY,
            review_id TEXT NOT NULL UNIQUE,
            approval_id TEXT NOT NULL UNIQUE,
            idempotency_key TEXT NOT NULL UNIQUE,
            shop_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            approved_reviewer_id TEXT NOT NULL,
            draft_sha256 TEXT NOT NULL,
            candidate_sha256 TEXT NOT NULL,
            media_snapshot_sha256 TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN
              ('READY','LEASED','SUCCEEDED','DEAD','REVOKED')),
            created_ms INTEGER NOT NULL,
            next_retry_ms INTEGER NOT NULL,
            attempt INTEGER NOT NULL DEFAULT 0,
            fence TEXT,
            lease_expires_ms INTEGER,
            result_sha256 TEXT,
            completed_ms INTEGER
          );
          CREATE INDEX IF NOT EXISTS f7_dispatch_next
            ON f7_approved_edit_dispatch(shop_id,state,next_retry_ms);
        """)

    def close(self):
        self.db.close()

    def _transaction(self, f):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            result = f()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    @staticmethod
    def _ctx(context: CurrentReviewContext) -> CurrentReviewContext:
        if not isinstance(context, CurrentReviewContext):
            raise ReviewStateError("Trusted current JWT/rights context required")
        return context.validated()

    def stage_approved(self, *, context, review_id, approval_id,
                       draft_sha256, candidate_sha256, human_confirmed,
                       now_ms=None):
        """Only enqueue AFTER verifying persisted human approval, never browser intent.

        True production code must bind this INSERT to the same Postgres
        transaction that writes the authoritative human approval/audit.
        """
        ctx = self._ctx(context)
        now = _clock(now_ms)
        _identifier(review_id, "review id")
        _identifier(approval_id, "approval id")
        _digest(draft_sha256, "draft")
        _digest(candidate_sha256, "candidate")
        if human_confirmed is not True:
            raise ReviewStateError("Persisted explicit human confirmation required")
        dispatch_id = ID_PREFIX + secrets.token_hex(16)
        # One stable idempotency key for one reviewed approval. It must be
        # carried downstream to Feature4 even if the lease is replayed.
        idempotency_key = "f7job_" + secrets.token_hex(16)

        def write():
            # Both tables MUST exist in the SAME SQLite database so approval
            # verification and the outbox INSERT are one atomic transaction.
            # A caller's human_confirmed=True boolean is never sufficient.
            try:
                approved = self.db.execute("""
                  SELECT * FROM feature7_local_reviews WHERE review_id=?
                """, (review_id,)).fetchone()
            except sqlite3.OperationalError as exc:
                raise ReviewStateError(
                    "Durable approved human review journal required"
                ) from exc
            if (approved is None or approved["status"] != "APPROVED" or
                    approved["approval_id"] != approval_id or
                    approved["reviewer_id"] != ctx.reviewer_id or
                    approved["shop_id"] != ctx.shop_id or
                    approved["campaign_id"] != ctx.campaign_id or
                    approved["media_snapshot_sha256"] != ctx.media_snapshot_sha256 or
                    approved["draft_sha256"] != draft_sha256 or
                    approved["candidate_sha256"] != candidate_sha256 or
                    approved["expires_ms"] is None or
                    not approved["created_ms"] <= now <= approved["expires_ms"]):
                raise ReviewStateError(
                    "Persisted, unexpired and matching human approval required"
                )
            if self.db.execute(
                "SELECT 1 FROM f7_approved_edit_dispatch WHERE "
                "review_id=? OR approval_id=?", (review_id, approval_id)
            ).fetchone():
                raise ReviewStateError("Approval already staged for dispatch")
            self.db.execute("""
              INSERT INTO f7_approved_edit_dispatch
              (dispatch_id,review_id,approval_id,idempotency_key,
               shop_id,campaign_id,approved_reviewer_id,
               draft_sha256,candidate_sha256,media_snapshot_sha256,
               state,created_ms,next_retry_ms)
              VALUES (?,?,?,?,?,?,?,?,?,?,'READY',?,?)
            """, (dispatch_id, review_id, approval_id, idempotency_key,
                  ctx.shop_id, ctx.campaign_id, ctx.reviewer_id,
                  draft_sha256, candidate_sha256, ctx.media_snapshot_sha256,
                  now, now))
            return {"dispatch_id": dispatch_id, "idempotency_key": idempotency_key,
                    "state": "READY", "attempt": 0, "approved": False}

        return self._transaction(write)

    def _scope(self, row, ctx):
        if (row["shop_id"] != ctx.shop_id or
                row["campaign_id"] != ctx.campaign_id or
                row["media_snapshot_sha256"] != ctx.media_snapshot_sha256):
            raise ReviewStateError("Changed, foreign or revoked private media scope")

    def _approval_live(self, row, now):
        persisted = self.db.execute("""
          SELECT * FROM feature7_local_reviews WHERE review_id=?
        """, (row["review_id"],)).fetchone()
        if (persisted is None or persisted["status"] != "APPROVED" or
                persisted["approval_id"] != row["approval_id"] or
                persisted["shop_id"] != row["shop_id"] or
                persisted["campaign_id"] != row["campaign_id"] or
                persisted["reviewer_id"] != row["approved_reviewer_id"] or
                persisted["media_snapshot_sha256"] != row["media_snapshot_sha256"] or
                persisted["draft_sha256"] != row["draft_sha256"] or
                persisted["candidate_sha256"] != row["candidate_sha256"] or
                persisted["expires_ms"] is None or
                not persisted["created_ms"] <= now <= persisted["expires_ms"]):
            raise ReviewStateError(
                "Human approval expired, revoked or changed during dispatch")

    def lease_next(self, *, context, now_ms=None, lease_ms=LEASE_MS):
        ctx = self._ctx(context)
        now = _clock(now_ms)
        if type(lease_ms) is not int or not 1000 <= lease_ms <= LEASE_MS:
            raise ReviewStateError("Invalid bounded dispatch lease")

        def claim():
            # Revoke stale/withdrawn approvals BEFORE choosing a ready lease.
            # This is the same SQLite transaction as the lease write.
            self.db.execute("""
              UPDATE f7_approved_edit_dispatch
              SET state='REVOKED',fence=NULL,lease_expires_ms=NULL
              WHERE shop_id=? AND campaign_id=?
                AND media_snapshot_sha256=?
                AND state IN ('READY','LEASED')
                AND NOT EXISTS (
                  SELECT 1 FROM feature7_local_reviews a
                  WHERE a.review_id=f7_approved_edit_dispatch.review_id
                    AND a.status='APPROVED'
                    AND a.approval_id=f7_approved_edit_dispatch.approval_id
                    AND a.reviewer_id=f7_approved_edit_dispatch.approved_reviewer_id
                    AND a.shop_id=f7_approved_edit_dispatch.shop_id
                    AND a.campaign_id=f7_approved_edit_dispatch.campaign_id
                    AND a.media_snapshot_sha256=
                      f7_approved_edit_dispatch.media_snapshot_sha256
                    AND a.draft_sha256=f7_approved_edit_dispatch.draft_sha256
                    AND a.candidate_sha256=f7_approved_edit_dispatch.candidate_sha256
                    AND a.expires_ms>=?
                )
            """, (ctx.shop_id,ctx.campaign_id,
                  ctx.media_snapshot_sha256,now))
            # A worker can crash during its final permitted attempt.
            # Reap that terminal expired lease instead of stranding a job
            # permanently in LEASED without a visible DEAD state.
            self.db.execute("""
              UPDATE f7_approved_edit_dispatch
              SET state='DEAD',fence=NULL,lease_expires_ms=NULL
              WHERE shop_id=? AND campaign_id=?
                AND media_snapshot_sha256=?
                AND state='LEASED' AND attempt>=?
                AND lease_expires_ms<=?
            """, (ctx.shop_id, ctx.campaign_id,
                  ctx.media_snapshot_sha256, MAX_ATTEMPTS, now))
            row = self.db.execute("""
              SELECT * FROM f7_approved_edit_dispatch
              WHERE shop_id=? AND campaign_id=?
                AND media_snapshot_sha256=?
                AND attempt<?
                AND ((state='READY' AND next_retry_ms<=?)
                  OR (state='LEASED' AND lease_expires_ms<=?))
              ORDER BY created_ms,dispatch_id LIMIT 1
            """, (ctx.shop_id, ctx.campaign_id,
                  ctx.media_snapshot_sha256, MAX_ATTEMPTS, now, now)).fetchone()
            if row is None:
                return None
            next_attempt = row["attempt"] + 1
            fence = secrets.token_hex(16)
            changed = self.db.execute("""
              UPDATE f7_approved_edit_dispatch
              SET state='LEASED',attempt=?,fence=?,lease_expires_ms=?
              WHERE dispatch_id=? AND attempt=?
            """, (next_attempt, fence, now + lease_ms, row["dispatch_id"], row["attempt"]))
            if changed.rowcount != 1:
                raise ReviewStateError("Concurrent dispatch attempt changed")
            return DispatchLease(
                dispatch_id=row["dispatch_id"],
                idempotency_key=row["idempotency_key"],
                attempt=next_attempt, fence=fence, expires_ms=now + lease_ms,
                shop_id=ctx.shop_id, campaign_id=ctx.campaign_id,
                draft_sha256=row["draft_sha256"],
                candidate_sha256=row["candidate_sha256"])

        return self._transaction(claim)

    def _leased(self, row, ctx, lease, now):
        self._scope(row, ctx)
        self._approval_live(row,now)
        if (not isinstance(lease, DispatchLease) or
                row["dispatch_id"] != lease.dispatch_id or
                row["idempotency_key"] != lease.idempotency_key or
                row["state"] != "LEASED" or
                row["attempt"] != lease.attempt or
                row["fence"] != lease.fence or
                row["lease_expires_ms"] != lease.expires_ms or
                now >= row["lease_expires_ms"]):
            raise ReviewStateError("Expired, foreign or stale worker fencing token")

    def heartbeat(self, *, context, lease, now_ms=None, lease_ms=LEASE_MS):
        ctx = self._ctx(context)
        now = _clock(now_ms)
        if type(lease_ms) is not int or not 1000 <= lease_ms <= LEASE_MS:
            raise ReviewStateError("Invalid heartbeat lease")
        def extend():
            row = self.db.execute(
                "SELECT * FROM f7_approved_edit_dispatch WHERE dispatch_id=?",
                (lease.dispatch_id,)).fetchone()
            if row is None:
                raise ReviewStateError("Unknown dispatch")
            self._leased(row, ctx, lease, now)
            # A short heartbeat must never reduce an already granted lease:
            # otherwise a second worker could reclaim while the first is live.
            # Keep the original fence and expiry unless this heartbeat extends.
            new_expiry = max(row["lease_expires_ms"], now + lease_ms)
            if new_expiry != row["lease_expires_ms"]:
                self.db.execute(
                    "UPDATE f7_approved_edit_dispatch SET lease_expires_ms=? "
                    "WHERE dispatch_id=?", (new_expiry, lease.dispatch_id))
            return DispatchLease(lease.dispatch_id, lease.idempotency_key,
                                 lease.attempt, lease.fence, new_expiry,
                                 lease.shop_id, lease.campaign_id,
                                 lease.draft_sha256, lease.candidate_sha256)
        return self._transaction(extend)

    def finish(self, *, context, lease, result_sha256, now_ms=None):
        ctx = self._ctx(context)
        now = _clock(now_ms)
        _digest(result_sha256, "private render result")
        def complete():
            row = self.db.execute(
                "SELECT * FROM f7_approved_edit_dispatch WHERE dispatch_id=?",
                (lease.dispatch_id,)).fetchone()
            if row is None:
                raise ReviewStateError("Unknown dispatch")
            self._leased(row, ctx, lease, now)
            self.db.execute("""
              UPDATE f7_approved_edit_dispatch
              SET state='SUCCEEDED',result_sha256=?,completed_ms=?,
                fence=NULL,lease_expires_ms=NULL
              WHERE dispatch_id=?
            """, (result_sha256, now, lease.dispatch_id))
            return {"dispatch_id": lease.dispatch_id,
                    "idempotency_key": lease.idempotency_key,
                    "state": "SUCCEEDED", "result_sha256": result_sha256}
        return self._transaction(complete)

    def fail_and_retry(self, *, context, lease, now_ms=None, retry_delay_ms=1000):
        ctx = self._ctx(context)
        now = _clock(now_ms)
        if type(retry_delay_ms) is not int or not 100 <= retry_delay_ms <= 60000:
            raise ReviewStateError("Invalid retry delay")
        def retry():
            row = self.db.execute(
                "SELECT * FROM f7_approved_edit_dispatch WHERE dispatch_id=?",
                (lease.dispatch_id,)).fetchone()
            if row is None:
                raise ReviewStateError("Unknown dispatch")
            self._leased(row, ctx, lease, now)
            state = "DEAD" if row["attempt"] >= MAX_ATTEMPTS else "READY"
            self.db.execute("""
              UPDATE f7_approved_edit_dispatch
              SET state=?,next_retry_ms=?,fence=NULL,lease_expires_ms=NULL
              WHERE dispatch_id=?
            """, (state, now + retry_delay_ms, lease.dispatch_id))
            return {"state": state, "idempotency_key": lease.idempotency_key}
        return self._transaction(retry)

    def revoke(self, *, context, dispatch_id):
        ctx = self._ctx(context)
        _identifier(dispatch_id, "dispatch")
        def cancel():
            row = self.db.execute(
                "SELECT * FROM f7_approved_edit_dispatch WHERE dispatch_id=?",
                (dispatch_id,)).fetchone()
            if row is None:
                raise ReviewStateError("Unknown dispatch")
            self._scope(row, ctx)
            if row["state"] == "SUCCEEDED":
                raise ReviewStateError("Already completed: cannot revoke a delivered output")
            if row["state"] == "REVOKED":
                raise ReviewStateError("Already revoked")
            self.db.execute(
                "UPDATE f7_approved_edit_dispatch SET state='REVOKED',"
                "fence=NULL,lease_expires_ms=NULL WHERE dispatch_id=?",
                (dispatch_id,))
            return {"state": "REVOKED", "dispatch_id": dispatch_id}
        return self._transaction(cancel)

    def reconcile_by_idempotency(self, *, context, idempotency_key):
        """Read-only uncertainty resolution. Never blindly resubmit on timeout.

        A different shop, campaign or changed source cannot discover a
        result by knowing the idempotency key. This is not public HTTP.
        """
        ctx = self._ctx(context)
        _identifier(idempotency_key, "idempotency key")
        row = self.db.execute("""
          SELECT * FROM f7_approved_edit_dispatch
          WHERE idempotency_key=?
        """, (idempotency_key,)).fetchone()
        if row is None:
            raise ReviewStateError("Unknown private dispatch")
        self._scope(row, ctx)
        return {"dispatch_id": row["dispatch_id"], "state": row["state"],
                "attempt": row["attempt"],
                "idempotency_key": row["idempotency_key"],
                "result_sha256": row["result_sha256"]}

    def inspect(self, *, context, dispatch_id):
        ctx = self._ctx(context)
        _identifier(dispatch_id, "dispatch")
        row = self.db.execute("SELECT * FROM f7_approved_edit_dispatch "
                              "WHERE dispatch_id=?", (dispatch_id,)).fetchone()
        if row is None:
            raise ReviewStateError("Unknown dispatch")
        self._scope(row, ctx)
        return {"state": row["state"], "attempt": row["attempt"],
                "idempotency_key": row["idempotency_key"],
                "result_sha256": row["result_sha256"]}
