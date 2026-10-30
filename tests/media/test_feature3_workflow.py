"""Feature #3 CPU worker contract tests; no hosted Azure, Supabase or GPU calls."""
from __future__ import annotations
from dataclasses import replace
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from studio_v2 import DesignError, compose_poster
from render_workflow_v2 import (
    PosterJobBlocked, PosterJobTicket, design_fingerprint, execute_cpu_poster,
)


class CPUWorkerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.stage = self.root / "stage"
        self.scratch = self.root / "scratch"
        self.stage.mkdir()
        self.scratch.mkdir()
        self.shop, self.campaign, self.day, self.draft, self.job_id = (
            str(uuid4()) for _ in range(5)
        )
        self.asset = str(uuid4())
        Image.new("RGB", (180, 220), "#CDA785").save(self.stage / "cloth.png")
        self.doc = compose_poster(
            shop_id=self.shop, mode="image", prompt="Festive clothing",
            business_name="Golden Boutique", headline="New fashion edit",
            source_asset_id=self.asset, approved_offer="20% OFF",
        )
        self.ticket = PosterJobTicket(
            shop_id=self.shop, campaign_id=self.campaign, day_id=self.day,
            draft_id=self.draft, job_id=self.job_id, draft_revision=2,
            design_sha256=design_fingerprint(self.doc),
        )
        self.manifest = {
            "shop_id": self.shop,
            "assets": {
                self.asset: {
                    "shop_id": self.shop, "kind": "image", "path": "cloth.png",
                    "rights": {"license": "owned", "commercial_use": True,
                               "source": "synthetic-worker-test",
                               "evidence": "local Pillow fixture"},
                },
            },
        }
        self.events = []
        self.claimed = set()

    def claim(self, job):
        if job.job_id in self.claimed:
            return None
        self.claimed.add(job.job_id)
        self.events.append("claim")
        return "verified-lease-for-test-run"

    def authorize(self, job, asset_ids, lease):
        self.events.append("rights-rechecked")
        self.assertEqual(job.shop_id, self.shop)
        self.assertEqual(asset_ids, (self.asset,))
        return self.manifest, self.stage

    def writer(self, job, lease, path, key, meta):
        self.events.append("private-write")
        self.assertTrue(path.exists())
        self.assertIn("/posters-v2/" + job.job_id + "/", key)
        self.assertTrue(meta["private"])
        self.assertFalse(meta["inference"])
        self.assertEqual(meta["rights_checked_asset_ids"], [self.asset])
        data = path.read_bytes()
        self.assertGreater(len(data), 1000)
        return {"asset_id": str(uuid4()), "object_key": key}

    def complete(self, job, lease, receipt):
        self.events.append("commit-fenced")
        self.assertEqual(receipt["shop_id"], self.shop)

    def failure(self, job, lease, code):
        self.events.append("failed-fenced")
        self.assertEqual(code, "POSTER_V2_CPU_RENDER_FAILED")

    def execute_ticket(self, job=None, **changes):
        params = dict(
            claim_job=self.claim, authorize_staged_assets=self.authorize,
            write_private_media=self.writer, complete_job=self.complete,
            fail_job=self.failure, trusted_scratch_root=self.scratch,
        )
        params.update(changes)
        return execute_cpu_poster(job or self.ticket, self.doc, **params)

    def test_private_png_and_fenced_order(self):
        info = self.execute_ticket()
        self.assertEqual(info["status"], "SUCCEEDED")
        self.assertEqual(info["output_format"], "png")
        self.assertEqual(self.events,
                         ["claim", "rights-rechecked", "private-write", "commit-fenced"])
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_retry_same_job_does_not_duplicate_storage(self):
        self.execute_ticket()
        self.events.clear()
        with self.assertRaisesRegex(PosterJobBlocked, "lease unavailable"):
            self.execute_ticket()
        self.assertEqual(self.events, [])

    def test_stale_draft_foreign_shop_and_wrong_hash_are_preclaim_denied(self):
        other = replace(self.ticket, shop_id=str(uuid4()))
        with self.assertRaisesRegex(PosterJobBlocked, "Cross-tenant"):
            self.execute_ticket(other)
        wrong = replace(self.ticket, design_sha256="f" * 64)
        with self.assertRaisesRegex(PosterJobBlocked, "fingerprint"):
            self.execute_ticket(wrong)
        older = replace(self.ticket, draft_revision=0)
        with self.assertRaisesRegex(PosterJobBlocked, "revision"):
            self.execute_ticket(older)
        unknown = replace(self.ticket, output_format="svg")
        with self.assertRaisesRegex(PosterJobBlocked, "format"):
            self.execute_ticket(unknown)
        self.assertEqual(self.events, [])

    def test_forged_manifest_and_revoked_rights_are_rejected(self):
        with self.assertRaisesRegex(PosterJobBlocked, "manifest"):
            self.execute_ticket(authorize_staged_assets=lambda *_: ({
                "shop_id": str(uuid4()), "assets": {}
            }, self.stage))
        self.assertEqual(self.events, ["claim", "failed-fenced"])
        self.events.clear()
        self.claimed.clear()
        self.manifest["assets"][self.asset]["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(DesignError, "rights"):
            self.execute_ticket()
        self.assertEqual(self.events, ["claim", "rights-rechecked", "failed-fenced"])

    def test_bad_object_receipt_does_not_commit(self):
        with self.assertRaisesRegex(PosterJobBlocked, "receipt"):
            self.execute_ticket(write_private_media=lambda *_: {
                "asset_id": str(uuid4()), "object_key": "another-shop/public.png",
            })
        self.assertIn("failed-fenced", self.events)
        self.assertNotIn("commit-fenced", self.events)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg missing on media runner")
    def test_bounded_animated_mp4_through_private_worker(self):
        ticket = replace(self.ticket, output_format="mp4",
                         duration_seconds=1, fps=3)
        info = self.execute_ticket(ticket)
        self.assertEqual(info["output_format"], "mp4")
        self.assertEqual(info["status"], "SUCCEEDED")

    def test_bounded_gif_and_reject_excessive_animation(self):
        ticket = replace(self.ticket, output_format="gif",
                         duration_seconds=1, fps=3)
        info = self.execute_ticket(ticket)
        self.assertEqual(info["output_format"], "gif")
        oversize = replace(ticket, fps=15, duration_seconds=5)
        with self.assertRaisesRegex(PosterJobBlocked, "quota"):
            self.execute_ticket(oversize)


if __name__ == "__main__":
    unittest.main()
