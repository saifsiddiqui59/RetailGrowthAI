"""Feature7 local transaction journal for reviewed uploaded-footage edits.

This is a testable **single-machine integration example**, not Supabase, not
the public approval endpoint, and not an authentication mechanism. The caller
MUST derive CurrentReviewContext from current trusted JWT+RLS membership and
live media-rights checks, never the request body. Production coordinator must
replace this SQLite journal with an atomic tenant-fenced DB/outbox transaction.

No media/transcripts are stored: only namespaced identifiers and SHA256s.
This module does NOT publish, render, or make Feature4 approval authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import secrets
import sqlite3
import time
from pathlib import Path

IDENT = re.compile(r"^[A-Za-z0-9_-]{1,120}$")
DIGEST = re.compile(r"^[a-f0-9]{64}$")
TTL_MS = 10 * 60 * 1000


class ReviewStateError(ValueError):
    """Fail closed if a private edit is stale, reused, revoked or unauthorized."""


@dataclass(frozen=True)
class CurrentReviewContext:
    shop_id: str
    campaign_id: str
    reviewer_id: str
    role: str
    active_membership: bool
    video_rights_current: bool
    media_snapshot_sha256: str

    def validated(self):
        if (not all(isinstance(s, str) and IDENT.fullmatch(s)
                    for s in (self.shop_id, self.campaign_id, self.reviewer_id))
                or self.role not in ("OWNER", "EDITOR")
                or self.active_membership is not True
                or self.video_rights_current is not True
                or not isinstance(self.media_snapshot_sha256, str)
                or not DIGEST.fullmatch(self.media_snapshot_sha256)):
            raise ReviewStateError("Current trusted reviewer and rights required")
        return self


def _digest(value, name):
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise ReviewStateError(f"Invalid {name}")
    return value


def _identifier(value, name):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ReviewStateError(f"Invalid {name}")
    return value


def _clock(now_ms):
    now = int(time.time() * 1000) if now_ms is None else now_ms
    if type(now) is not int or now < 0:
        raise ReviewStateError("Invalid trusted time")
    return now


class LocalReviewJournal:
    """SQLite BEGIN IMMEDIATE + CAS for deterministic, offline failure tests.

    A server must use its own authenticated application context and durable
    shared PostgreSQL instead; a browser cannot select this file.
    """

    def __init__(self, database_file: str | Path):
        self.database_file = str(database_file)
        self.db = sqlite3.connect(self.database_file, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS feature7_local_reviews (
            review_id TEXT PRIMARY KEY,
            shop_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            draft_sha256 TEXT NOT NULL,
            candidate_sha256 TEXT NOT NULL,
            media_snapshot_sha256 TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
            status TEXT NOT NULL DEFAULT 'PENDING'
              CHECK (status IN ('PENDING','APPROVED','CONSUMED','REVOKED')),
            reviewer_id TEXT,
            approval_id TEXT UNIQUE,
            created_ms INTEGER NOT NULL,
            expires_ms INTEGER,
            consumed_ms INTEGER
          );
          CREATE INDEX IF NOT EXISTS idx_feature7_local_tenant
            ON feature7_local_reviews(shop_id,campaign_id,status);
        """)

    def close(self):
        self.db.close()

    def _begin(self):
        self.db.execute("BEGIN IMMEDIATE")

    def _row(self, review_id):
        row = self.db.execute(
            "SELECT * FROM feature7_local_reviews WHERE review_id=?",
            (review_id,)
        ).fetchone()
        if row is None:
            raise ReviewStateError("Missing private review")
        return row

    @staticmethod
    def _same_scope(row, context):
        if (row["shop_id"] != context.shop_id or
                row["campaign_id"] != context.campaign_id or
                row["media_snapshot_sha256"] != context.media_snapshot_sha256):
            raise ReviewStateError("Foreign, changed or revoked video rights")

    def stage(self, *, context, draft_sha256, candidate_sha256, now_ms=None):
        ctx = context.validated()
        now = _clock(now_ms)
        _digest(draft_sha256, "canonical draft digest")
        _digest(candidate_sha256, "reviewed candidate digest")
        review_id = "f7_" + secrets.token_hex(16)
        self._begin()
        try:
            self.db.execute("""
              INSERT INTO feature7_local_reviews
              (review_id,shop_id,campaign_id,draft_sha256,candidate_sha256,
               media_snapshot_sha256,created_ms)
              VALUES (?,?,?,?,?,?,?)
            """, (review_id, ctx.shop_id, ctx.campaign_id, draft_sha256,
                  candidate_sha256, ctx.media_snapshot_sha256, now))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return {"review_id": review_id, "revision": 0,
                "status": "PENDING", "approved": False}

    def approve(self, *, review_id, expected_revision, context,
                candidate_sha256, confirmed_by_human, now_ms=None):
        ctx = context.validated()
        now = _clock(now_ms)
        _identifier(review_id, "review id")
        _digest(candidate_sha256, "candidate digest")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ReviewStateError("Invalid expected revision")
        if confirmed_by_human is not True:
            raise ReviewStateError("Explicit real human approval required")
        self._begin()
        try:
            row = self._row(review_id)
            self._same_scope(row, ctx)
            if (row["status"] != "PENDING" or
                    row["revision"] != expected_revision or
                    row["candidate_sha256"] != candidate_sha256):
                raise ReviewStateError("Stale or changed review")
            approval_id = "f7a_" + secrets.token_hex(16)
            modified = self.db.execute("""
              UPDATE feature7_local_reviews
              SET status='APPROVED',revision=revision+1,reviewer_id=?,
                approval_id=?,expires_ms=?
              WHERE review_id=? AND status='PENDING' AND revision=?
            """, (ctx.reviewer_id, approval_id, now + TTL_MS,
                  review_id, expected_revision))
            if modified.rowcount != 1:
                raise ReviewStateError("Concurrent review change")
            self.db.execute("COMMIT")
            return {"approval_id": approval_id, "revision": expected_revision+1,
                    "expires_ms": now+TTL_MS, "status": "APPROVED"}
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def claim_for_feature4(self, *, review_id, approval_id, context,
                           draft_sha256, candidate_sha256,
                           expected_revision, now_ms=None):
        ctx = context.validated()
        now = _clock(now_ms)
        _identifier(review_id, "review id")
        _identifier(approval_id, "approval id")
        _digest(draft_sha256, "canonical draft hash")
        _digest(candidate_sha256, "candidate hash")
        if type(expected_revision) is not int or expected_revision < 1:
            raise ReviewStateError("Invalid claim revision")
        self._begin()
        try:
            row = self._row(review_id)
            self._same_scope(row, ctx)
            if (row["status"] != "APPROVED" or
                    row["revision"] != expected_revision or
                    row["approval_id"] != approval_id or
                    row["reviewer_id"] != ctx.reviewer_id or
                    row["draft_sha256"] != draft_sha256 or
                    row["candidate_sha256"] != candidate_sha256 or
                    row["expires_ms"] is None or now > row["expires_ms"] or
                    now < row["created_ms"]):
                raise ReviewStateError("Stale, expired, foreign or already used approval")
            modified = self.db.execute("""
              UPDATE feature7_local_reviews
              SET status='CONSUMED',revision=revision+1,consumed_ms=?
              WHERE review_id=? AND status='APPROVED' AND revision=?
            """, (now, review_id, expected_revision))
            if modified.rowcount != 1:
                raise ReviewStateError("Already claimed")
            self.db.execute("COMMIT")
            # The worker must additionally verify the signed JS edit receipt
            # and canonical Feature4 Python draft_fingerprint before rendering.
            return {"approval_id": approval_id, "shop_id": ctx.shop_id,
                    "campaign_id": ctx.campaign_id,
                    "draft_sha256": draft_sha256,
                    "candidate_sha256": candidate_sha256,
                    "status": "CLAIMED_ONCE", "revision": expected_revision+1}
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def revoke(self, *, review_id, context, expected_revision):
        ctx = context.validated()
        _identifier(review_id, "review id")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ReviewStateError("Invalid revision")
        self._begin()
        try:
            row = self._row(review_id)
            self._same_scope(row, ctx)
            if row["status"] not in ("PENDING", "APPROVED") or row["revision"] != expected_revision:
                raise ReviewStateError("Already consumed, revoked or stale")
            modified = self.db.execute("""
              UPDATE feature7_local_reviews
              SET status='REVOKED',revision=revision+1
              WHERE review_id=? AND revision=?
            """, (review_id, expected_revision))
            if modified.rowcount != 1:
                raise ReviewStateError("Concurrent revocation")
            self.db.execute("COMMIT")
            return {"review_id": review_id, "status": "REVOKED"}
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
