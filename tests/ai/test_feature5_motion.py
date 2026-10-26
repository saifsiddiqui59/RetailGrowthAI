"""Feature #5 offline tests. No GPUs, model downloads, Azure or provider billing."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from feature5_motion.contracts import AssetGrant, MotionSpec, MotionError, estimate_cost, validate_source
from feature5_motion.runner import HunyuanLocalRunner
from feature5_motion.worker import MotionWorker, validate_clip


def uid():
    return str(uuid4())


class TestMotionContracts(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset = uid(), uid(), uid()

    def spec(self, **kw):
        args = dict(job_id=self.job, shop_id=self.shop, prompt="Adult model walking in a boutique", mode="text")
        args.update(kw)
        return MotionSpec(**args)

    def grant(self, **kw):
        args = dict(asset_id=self.asset, shop_id=self.shop, approved=True,
                    private=True, commercial_rights=True, media_type="image/png", clean_layers=True)
        args.update(kw)
        return AssetGrant(**args)

    def test_text_mode(self):
        spec = self.spec()
        validate_source(spec, None)
        self.assertEqual(spec.duration_seconds, 5)

    def test_image_and_poster_mode(self):
        for mode in ("image", "poster"):
            spec = self.spec(mode=mode, source_asset_id=self.asset)
            validate_source(spec, self.grant())
            self.assertEqual(spec.mode, mode)

    def test_cross_tenant_and_unapproved_rejected(self):
        spec = self.spec(mode="image", source_asset_id=self.asset)
        for grant in (self.grant(shop_id=uid()), self.grant(approved=False),
                      self.grant(private=False), self.grant(commercial_rights=False),
                      self.grant(asset_id=uid()), self.grant(media_type="video/mp4")):
            with self.assertRaises(MotionError):
                validate_source(spec, grant)

    def test_poster_requires_clean_visual(self):
        with self.assertRaises(MotionError):
            validate_source(self.spec(mode="poster", source_asset_id=self.asset),
                            self.grant(clean_layers=False))

    def test_invalid_mode_and_image(self):
        for data in ({"mode": "video"}, {"mode": "image"},
                     {"mode": "text", "source_asset_id": self.asset},
                     {"mode": "image", "source_asset_id": "http://evil.invalid/a.png"}):
            with self.assertRaises(MotionError):
                self.spec(**data)

    def test_bounded_generation_settings(self):
        for changes in ({"duration_seconds": 30}, {"resolution": "1080p"},
                        {"fps": 30}, {"aspect_ratio": "4:3"}, {"seed": -1},
                        {"prompt": ""}, {"prompt": "x" * 1501},
                        {"job_id": "../not-a-uuid"}, {"prompt_version": "unreviewed"}):
            with self.assertRaises(MotionError):
                self.spec(**changes)

    def test_budget_includes_coldstart_storage_egress(self):
        estimate = estimate_cost(gpu_usd_hour="1", cpu_usd_hour="0.2", gpu_seconds=120,
                                 cold_start_seconds=60, cpu_seconds=60,
                                 storage_gb="0.1", storage_usd_gb="0.02",
                                 egress_gb="0.05", egress_usd_gb="0.10")
        self.assertEqual(str(estimate.gpu_compute_usd), "0.0500")
        self.assertEqual(str(estimate.total_usd), "0.0604")

    def test_cost_negative_or_nan_rejected(self):
        for cost in ("-2", "NaN", "Infinity", "abc"):
            with self.assertRaises(MotionError):
                estimate_cost(gpu_usd_hour=cost, cpu_usd_hour="0", gpu_seconds=5, cold_start_seconds=1)


class TestGpuRunner(unittest.TestCase):
    def setUp(self):
        self.spec = MotionSpec(job_id=uid(), shop_id=uid(), prompt="Luxury boutique", mode="text")

    def test_no_gpu_no_cost_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            wd = Path(temp)
            runner = HunyuanLocalRunner(checkout=wd, weights=wd)
            with self.assertRaises(MotionError):
                runner.run(self.spec, source_file=None, workdir=wd)

    def test_approved_gate_still_requires_existing_model(self):
        with tempfile.TemporaryDirectory() as temp:
            wd = Path(temp)
            runner = HunyuanLocalRunner(checkout=wd, weights=wd, enabled=True,
                                        license_approved=True, gpu_budget_approved=True)
            with self.assertRaises(MotionError):
                runner.run(self.spec, source_file=None, workdir=wd)

    def test_timeout_boundaries(self):
        for seconds in (0, 29, 3601):
            with self.assertRaises(MotionError):
                HunyuanLocalRunner(checkout=Path("."), weights=Path("."), timeout_seconds=seconds)


class TestMediaValidation(unittest.TestCase):
    def test_valid_local_media_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            clip = Path(temp) / "clip.mp4"
            clip.write_bytes(b"synthetic-placeholder")
            data = {"format": {"duration": "5.01"}, "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 480,
                 "height": 832, "r_frame_rate": "24/1"}]}
            with patch("feature5_motion.worker.subprocess.run",
                       return_value=Mock(stdout=json.dumps(data).encode())) as probe:
                self.assertEqual(validate_clip(clip)["codec"], "h264")
                self.assertIn("-protocol_whitelist", probe.call_args.args[0])
                self.assertIn("file", probe.call_args.args[0])

    def test_probe_invalid_codec_fps_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            clip = Path(temp) / "clip.mp4"
            clip.write_bytes(b"fixture")
            for change in ({"duration": "25"}, {"codec_name": "vp9"}, {"r_frame_rate": "30/1"}):
                stream = {"codec_type": "video", "codec_name": "h264",
                          "width": 480, "height": 832, "r_frame_rate": "24/1"}
                duration = change.pop("duration", "5")
                stream.update(change)
                with patch("feature5_motion.worker.subprocess.run", return_value=Mock(
                    stdout=json.dumps({"format": {"duration": duration}, "streams": [stream]}).encode()
                )):
                    with self.assertRaises(MotionError):
                        validate_clip(clip)

    def test_invalid_or_untrusted_file_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            clip = Path(temp) / "clip.txt"
            clip.write_bytes(b"not an mp4")
            with self.assertRaises(MotionError):
                validate_clip(clip)


class TestMotionWorker(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset, self.token = uid(), uid(), uid(), uid()
        self.spec = MotionSpec(job_id=self.job, shop_id=self.shop, prompt="Adult model fashion walk",
                               mode="image", source_asset_id=self.asset)
        self.grant = AssetGrant(self.asset, self.shop, True, True, True, "image/png")
        self.store = Mock()
        self.media = Mock()
        self.runner = Mock()
        self.store.claim.return_value = {"attempt_token": self.token, "spec": self.spec,
                                         "reserved_usd": 0.1, "review_status": "APPROVED"}
        self.store.complete.return_value = True
        self.store.fail.return_value = True
        self.media.grant.return_value = self.grant
        self.media.upload_private.return_value = {"shop_id": self.shop, "job_id": self.job}

    def test_no_claim_no_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            self.store.claim.return_value = None
            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1)
            self.assertEqual(worker.execute(self.job), "NOT_CLAIMED")
            self.runner.run.assert_not_called()

    def test_no_budget_or_approval_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
                                  workdir_root=Path(temp), enabled=False, credit_cap_usd=1)
            with self.assertRaises(MotionError):
                worker.execute(self.job)
            self.store.claim.assert_not_called()
            worker.enabled = True
            self.store.claim.return_value["review_status"] = "DRAFT"
            with self.assertRaises(MotionError):
                worker.execute(self.job)
            self.runner.run.assert_not_called()

    def test_foreign_asset_does_not_start_gpu(self):
        with tempfile.TemporaryDirectory() as temp:
            self.media.grant.return_value = AssetGrant(self.asset, uid(), True, True, True, "image/png")
            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1)
            self.assertEqual(worker.execute(self.job), "FAILED")
            self.runner.run.assert_not_called()
            self.media.upload_private.assert_not_called()
            self.store.fail.assert_called_once()

    def test_successful_mock_contract_no_real_inference(self):
        with tempfile.TemporaryDirectory() as temp:
            self.media.stage.side_effect = lambda shop, asset, wd: wd / "source.png"
            def fake_run(spec, *, source_file, workdir):
                out = workdir / "motion.mp4"
                out.write_bytes(b"mock-not-real-media")
                return out
            self.runner.run.side_effect = fake_run
            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1)
            with patch("feature5_motion.worker.validate_clip", return_value={
                "codec": "h264", "duration_seconds": 5, "fps": 24}):
                self.assertEqual(worker.execute(self.job), "SUCCEEDED")
            self.store.complete.assert_called_once()
            metadata = self.media.upload_private.call_args.args[4]
            self.assertTrue(metadata["quality_review_required"])
            self.assertEqual(metadata["source_asset_id"], self.asset)

    def test_non_private_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            self.runner.run.side_effect = lambda spec, *, source_file, workdir: workdir / "motion.mp4"
            self.media.upload_private.return_value = {"shop_id": uid(), "job_id": self.job}
            worker = MotionWorker(store=self.store, media=self.media, runner=self.runner,
                                  workdir_root=Path(temp), enabled=True, credit_cap_usd=1)
            with patch("feature5_motion.worker.validate_clip", return_value={"codec": "h264"}):
                self.assertEqual(worker.execute(self.job), "FAILED")
            self.store.complete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
