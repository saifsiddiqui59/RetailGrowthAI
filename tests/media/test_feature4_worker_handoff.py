"""Feature #4 integration seam tests: fake existing Azure/Supabase services, no cloud secrets.

These are not hosted E2E tests. Confirm the worker cannot trust a browser
manifest, lose a tenant fence, double-claim/bill or expose unapproved output.
"""
import copy
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
import feature4_worker_handoff
from feature4_worker_handoff import (  # noqa: E402
    Feature4ClaimBusy, Feature4HandoffError, process_feature4_render,
    _staged_fingerprint, MAX_TOTAL_STAGED_BYTES,
)

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "44444444-4444-4444-8444-444444444444"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
JOB = "33333333-3333-4333-8333-333333333333"
LEASE = "55555555-5555-4555-8555-555555555555"


def sample():
    claim = {"id": JOB, "shop_id": SHOP, "campaign_id": CAMPAIGN,
             "idempotency_key": "approved-reel-01", "render_claim_token": LEASE,
             "preset": "feature4_reel_v1"}
    request = {
        "version": "creative_reel_v1", "shop_id": SHOP,
        "campaign_id": CAMPAIGN, "video_job_id": JOB,
        "idempotency_key": "approved-reel-01",
        "duration_seconds": 15, "template": "cinematic",
        "output": {"format": "mp4", "width": 1080, "height": 1920, "fps": 24},
        "script": {"source_feature": "feature2", "approved": True,
                   "approval_id": "reviewed-script-01",
                   "approved_text": ["Diwali Sale", "20% OFF", "Visit Our Store"],
                   "cta": "Visit Our Store"},
        "brand": {"shop_name": "Verified Boutique", "primary_color": "#abcdef",
                  "logo_asset_id": None},
        "scenes": [
            {"order": 0, "start_time": 0, "duration": 5,
             "headline": "Diwali Sale", "asset_id": "product01",
             "asset_type": "image", "source_feature": "feature3"},
            {"order": 1, "start_time": 5, "duration": 5,
             "headline": "20% OFF", "asset_id": "product01",
             "asset_type": "image", "source_feature": "feature3"},
            {"order": 2, "start_time": 10, "duration": 5,
             "headline": "Visit Our Store"},
        ],
    }
    records = {"product01": {
        "shop_id": SHOP, "kind": "image", "source_feature": "feature3",
        "approved": True, "storage_bucket": "retailgrowth-media",
        "object_path": SHOP + "/approved/product01.png",
        "mime_type": "image/png", "license_name": "owned",
        "rights_evidence": "Merchant attestation independently reviewed",
        "rights_source": "retailer original photograph",
    }}
    return claim, {"request": request, "assets": records}


class Admin:
    def __init__(self, claim, bundle):
        self.claim, self.bundle = claim, bundle
        self.status = "QUEUED"
        self.authorized = True
        self.current = True
        self.can_finalize = True
        self.failures = []
        self.completions = []

    def render_status(self, job_id):
        assert job_id == JOB
        return self.status

    def claim_feature4_render(self, job_id):
        return self.claim

    def render_authorized(self, claim):
        return self.authorized

    def load_feature4_bundle(self, claim):
        return self.bundle

    def feature4_claim_current(self, claim):
        return self.current

    def complete_feature4_render(self, claim, key, proof, rendered_as):
        self.completions.append((claim, key, proof, rendered_as))
        if self.can_finalize:
            self.status = "SUCCEEDED"
        return self.can_finalize

    def render_failure(self, claim, error, permanent=False):
        self.failures.append((error, permanent))


class Media:
    def __init__(self):
        self.downloads = []
        self.uploads = []

    def download(self, sid, key, destination):
        self.downloads.append((sid, key, destination))
        destination.write_bytes(b"trusted synthetic media fixture")
        return destination

    def upload(self, sid, job_id, file_path, *, lease_token):
        assert file_path.read_bytes().startswith(b"synthetic MP4 bytes")
        self.uploads.append((sid, job_id, str(file_path), lease_token))
        return sid + "/renders/" + job_id + "/" + lease_token + ".mp4"


def fake_render(request, manifest, staged, output):
    assert request["shop_id"] == SHOP
    assert manifest["shop_id"] == SHOP
    assert all(not Path(x["path"]).is_absolute() for x in manifest["assets"].values())
    destination = output / (JOB + ".mp4")
    destination.write_bytes(b"synthetic MP4 bytes" + b"0"*1024)
    from creative_contract import render_inputs
    audit = render_inputs(request, manifest).audit
    return {"file_path": str(destination), "render_job_id": JOB,
            "idempotency_key": request["idempotency_key"],
            "rendered_as": audit["rendered_as"],
            "fallback_events": audit["fallback_events"],
            "output_probe": {"duration_seconds": 15.0,
                             "width": 1080, "height": 1920, "fps": 24,
                             "bytes": destination.stat().st_size,
                             "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                             "video_codec": "h264", "audio_codec": "aac"}}


class WorkerHandoffTests(unittest.TestCase):
    def setUp(self):
        claim, bundle = sample()
        self.admin = Admin(claim, bundle)
        self.media = Media()

    def run_worker(self):
        return process_feature4_render(JOB, self.admin, self.media, render_fn=fake_render)

    def test_success_claim_fenced_private_storage_no_secondary_billing(self):
        self.assertEqual(self.run_worker(), "SUCCEEDED")
        self.assertEqual(len(self.media.downloads), 1)
        self.assertEqual(self.media.downloads[0][0], SHOP)
        self.assertEqual(len(self.media.uploads), 1)
        self.assertEqual(self.media.uploads[0][-1], LEASE)
        self.assertEqual(len(self.admin.completions), 1)
        self.assertEqual(self.admin.completions[0][-1], "AUTHORIZED_ASSEMBLY")
        self.assertEqual(self.admin.failures, [])
        self.assertEqual(self.run_worker(), "ALREADY_FINAL")
        self.assertEqual(len(self.media.uploads), 1)

    def test_busy_job_never_downloads_or_uploads(self):
        self.admin.claim = None
        with self.assertRaises(Feature4ClaimBusy):
            self.run_worker()
        self.assertEqual(self.media.downloads, [])
        self.assertEqual(self.admin.failures, [])

    def test_auth_revocation_and_lost_claim_abort_without_public_output(self):
        self.admin.authorized = False
        self.assertEqual(self.run_worker(), "DENIED")
        self.assertEqual(self.admin.failures, [("ACCESS_REVOKED", True)])
        self.assertEqual(self.media.downloads, [])
        self.admin.authorized = True
        self.admin.failures.clear()
        self.admin.current = False
        self.assertEqual(self.run_worker(), "STALE")
        self.assertEqual(self.media.uploads, [])
        self.assertEqual(self.admin.completions, [])

    def test_stale_claim_preflight_denies_private_download_and_render(self):
        self.admin.current = False
        def forbidden_render(*args):
            self.fail("stale claim must never invoke CPU renderer")
        self.assertEqual(process_feature4_render(
            JOB, self.admin, self.media, render_fn=forbidden_render), "STALE")
        self.assertEqual(self.media.downloads, [])
        self.assertEqual(self.media.uploads, [])
        self.assertEqual(self.admin.failures, [])

    def test_claim_revoked_after_staging_never_reaches_cpu_renderer(self):
        # First lease check before downloading passes; second after stage fails.
        self.admin.claim_checks = 0
        def current(_claim):
            self.admin.claim_checks += 1
            return self.admin.claim_checks == 1
        self.admin.feature4_claim_current = current
        def forbidden_render(*args):
            self.fail("stale post-staging claim must never start CPU renderer")
        self.assertEqual(process_feature4_render(
            JOB, self.admin, self.media, render_fn=forbidden_render), "STALE")
        self.assertEqual(len(self.media.downloads), 1)
        self.assertEqual(self.media.uploads, [])
        self.assertEqual(self.admin.completions, [])
        self.assertEqual(self.admin.failures, [])

    def test_same_content_inode_replacement_during_hash_is_rejected(self):
        # A stable open FD still reads old bytes after same-content os.replace.
        with tempfile.TemporaryDirectory(prefix="f4-inode-") as folder:
            root = Path(folder)
            original = root / "asset.png"
            original.write_bytes(b"original synthetic bytes" * 100)
            original_bytes = original.read_bytes()
            make_digest = hashlib.sha256
            class ReplacingDigest:
                def __init__(self):
                    self.digest = make_digest()
                    self.changed = False
                def update(self, data):
                    self.digest.update(data)
                    if not self.changed:
                        self.changed = True
                        replacement = root / "new-asset.png"
                        replacement.write_bytes(original_bytes)
                        os.replace(replacement, original)
                def hexdigest(self):
                    return self.digest.hexdigest()
            with patch.object(feature4_worker_handoff.hashlib, "sha256",
                              side_effect=lambda: ReplacingDigest()):
                with self.assertRaisesRegex(
                        Feature4HandoffError, "path changed while hashing"):
                    _staged_fingerprint(original)

    def test_zero_or_oversized_staged_media_denied_before_hashing(self):
        with tempfile.TemporaryDirectory(prefix="f4-limit-") as folder:
            path = Path(folder) / "asset.mp4"
            path.write_bytes(b"")
            with self.assertRaisesRegex(Feature4HandoffError, "nonempty bounded"):
                _staged_fingerprint(path)
            with path.open("wb") as f:
                f.truncate(MAX_TOTAL_STAGED_BYTES + 1)
            with self.assertRaisesRegex(Feature4HandoffError, "nonempty bounded"):
                _staged_fingerprint(path)

    def test_uploaded_key_must_bind_exact_original_shop_job_and_lease(self):
        """An upload adapter response is not an authorization grant."""
        allowed = SHOP + "/renders/" + JOB + "/" + LEASE + ".mp4"
        invalid = (
            OTHER + "/renders/" + JOB + "/" + LEASE + ".mp4",
            SHOP + "/renders/" + OTHER + "/" + LEASE + ".mp4",
            SHOP + "/renders/" + JOB + "/" + OTHER + ".mp4",
            SHOP + "/renders/" + JOB + "/" + LEASE + ".mp4?token=foreign",
            SHOP + "/renders/" + JOB + "/../" + LEASE + ".mp4",
            "https://example.invalid/" + allowed,
            allowed.upper(), allowed + "/extra", None, "", {"object_path": allowed},
        )
        for returned in invalid:
            with self.subTest(returned=returned):
                claim, bundle = sample()
                self.admin = Admin(claim, bundle)
                class WrongUploadKey(Media):
                    def upload(media_self, sid, job_id, file_path, *, lease_token):
                        super().upload(sid, job_id, file_path, lease_token=lease_token)
                        return returned
                self.media = WrongUploadKey()
                with self.assertRaisesRegex(
                        Feature4HandoffError, "Private uploaded object does not match current claim"):
                    self.run_worker()
                # Local success may leave an orphan remote upload, but must
                # never complete the wrong object or create a signed URL.
                self.assertEqual(len(self.media.uploads), 1)
                self.assertEqual(self.admin.completions, [])
                self.assertEqual(self.admin.failures, [("INVALID_RENDER_INPUT", True)])
        claim, bundle = sample()
        self.admin = Admin(claim, bundle)
        self.media = Media()
        self.assertEqual(self.run_worker(), "SUCCEEDED")
        self.assertEqual(self.admin.completions[0][1], allowed)

    def test_fencing_race_on_finalization_has_no_signed_url(self):
        self.admin.can_finalize = False
        self.assertEqual(self.run_worker(), "STALE")
        self.assertEqual(len(self.media.uploads), 1)
        self.assertEqual(len(self.admin.completions), 1)

    def test_wrong_job_id_campaign_shop_or_idempotency_rejected(self):
        for field, value in [
            ("shop_id", OTHER), ("campaign_id", OTHER),
            ("video_job_id", OTHER), ("idempotency_key", "different"),
        ]:
            self.admin.bundle = copy.deepcopy(sample()[1])
            self.admin.bundle["request"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(Feature4HandoffError, "Claimed job"):
                self.run_worker()
        self.assertEqual(len(self.media.downloads), 0)

    def test_wrong_tenant_bucket_path_rights_or_provenance_rejected_before_download(self):
        for field, value in [
            ("shop_id", OTHER), ("storage_bucket", "public-bucket"),
            ("object_path", OTHER + "/private.png"),
            ("object_path", SHOP + "/../stolen.png"),
            ("license_name", "unspecified"),
            ("rights_evidence", ""), ("mime_type", "text/html"),
            ("approved", False), ("source_feature", "feature5"),
        ]:
            self.admin.bundle = copy.deepcopy(sample()[1])
            self.admin.bundle["assets"]["product01"][field] = value
            with self.subTest(field=field), self.assertRaises(Exception):
                self.run_worker()
        self.assertEqual(len(self.media.downloads), 0)
        self.assertEqual(len(self.media.uploads), 0)

    def test_ambiguous_encoded_or_dot_private_object_paths_denied_before_download(self):
        # All these names formerly passed the worker path prefix / '..'
        # segment checks, yet are not canonical signed source paths.
        for suffix in (
            "/approved/./asset.png", "/approved/%2e%2e/asset.png",
            "/approved/photo%2fother.png", "/approved/img.png?token=foreign",
            "/approved/img.png#signed", "/approved/control\n.png",
            "/approved/fi\u200ble.png", "/approved/space name.png",
            "/approved/../other.png", "/approved//image.png",
        ):
            with self.subTest(suffix=repr(suffix)):
                self.admin.bundle = copy.deepcopy(sample()[1])
                self.admin.bundle["assets"]["product01"]["object_path"] = SHOP + suffix
                with self.assertRaisesRegex(Feature4HandoffError,
                                            "Media storage path escapes tenant"):
                    self.run_worker()
                self.assertEqual(self.media.downloads, [])
                self.assertEqual(self.media.uploads, [])
        self.assertEqual(self.admin.completions, [])

    def test_canonical_nested_private_object_path_remains_supported(self):
        self.admin.bundle["assets"]["product01"]["object_path"] = (
            SHOP + "/approved/F4_Products/2026-10/Look_01.png")
        self.assertEqual(self.run_worker(), "SUCCEEDED")
        self.assertEqual(self.media.downloads[0][1], (
            SHOP + "/approved/F4_Products/2026-10/Look_01.png"))

    def test_bundle_extraneous_private_asset_fails_closed(self):
        self.admin.bundle["assets"]["unrelated"] = copy.deepcopy(
            self.admin.bundle["assets"]["product01"])
        with self.assertRaisesRegex(Feature4HandoffError, "unrelated"):
            self.run_worker()
        self.assertEqual(self.media.downloads, [])

    def test_local_staged_source_mutation_or_symlink_swap_fails_before_upload(self):
        # Genuine CPU render must consume unchanged original downloaded bytes;
        # a forged probe/result from a renderer is not a waiver.
        for variant in ("overwrite", "append", "symlink"):
            with self.subTest(variant=variant):
                self.media = Media()
                self.admin.failures.clear()
                self.admin.completions.clear()
                def swapped(request, manifest, staged, output):
                    result = fake_render(request, manifest, staged, output)
                    source = next(staged.iterdir())
                    if variant == "overwrite":
                        source.write_bytes(b"different synthetic source media")
                    elif variant == "append":
                        with source.open("ab") as stream:
                            stream.write(b"tampered")
                    else:
                        source.unlink()
                        source.symlink_to(output / (JOB + ".mp4"))
                    return result
                with self.assertRaises(Feature4HandoffError):
                    process_feature4_render(JOB, self.admin, self.media, render_fn=swapped)
                self.assertEqual(self.media.uploads, [])
                self.assertEqual(self.admin.completions, [])
                self.assertEqual(self.admin.failures, [("INVALID_RENDER_INPUT", True)])

    def test_original_input_same_byte_inode_swap_during_cpu_is_denied(self):
        # Regression: the original _staged_fingerprint returned size+SHA
        # only, so an identical-byte new inode between checks went unseen.
        def swapped(request, manifest, staged, output):
            result = fake_render(request, manifest, staged, output)
            source = next(staged.iterdir())
            original = source.read_bytes()
            replacement = staged / "different-inode.png"
            replacement.write_bytes(original)
            os.replace(replacement, source)
            return result
        with self.assertRaisesRegex(Feature4HandoffError, "staged media changed"):
            process_feature4_render(JOB, self.admin, self.media, render_fn=swapped)
        self.assertEqual(self.media.uploads, [])
        self.assertEqual(self.admin.completions, [])
        self.assertEqual(self.admin.failures, [("INVALID_RENDER_INPUT", True)])

    def test_verified_output_cannot_change_during_private_upload(self):
        for variant in ("append", "overwrite", "same-byte-atomic-swap"):
            with self.subTest(variant=variant):
                self.media = Media()
                self.admin.failures.clear()
                self.admin.completions.clear()
                class CorruptDuringUpload(Media):
                    def upload(media_self, sid, job_id, file_path, *, lease_token):
                        key = super().upload(sid, job_id, file_path,
                                             lease_token=lease_token)
                        if variant == "append":
                            with file_path.open("ab") as out:
                                out.write(b"late data")
                        elif variant == "overwrite":
                            file_path.write_bytes(b"changed output" * 100)
                        else:
                            replacement = file_path.parent / "new-inode-output.mp4"
                            replacement.write_bytes(file_path.read_bytes())
                            os.replace(replacement, file_path)
                        return key
                self.media = CorruptDuringUpload()
                with self.assertRaisesRegex(
                        Feature4HandoffError, "Encoded output changed during private upload"):
                    self.run_worker()
                # An orphan upload can exist, but completion MUST NOT occur.
                self.assertEqual(len(self.media.uploads), 1)
                self.assertEqual(self.admin.completions, [])
                self.assertEqual(self.admin.failures, [("INVALID_RENDER_INPUT", True)])

    def test_renderer_wrong_output_or_cross_job_denied(self):
        def malicious(*args):
            result = fake_render(*args)
            result["idempotency_key"] = "another-tenant"
            return result
        with self.assertRaisesRegex(Feature4HandoffError, "Renderer output"):
            process_feature4_render(JOB, self.admin, self.media, render_fn=malicious)
        self.assertEqual(self.media.uploads, [])

    def test_rejected_unsigned_script_never_downloads(self):
        self.admin.bundle["request"]["script"]["approved"] = False
        with self.assertRaisesRegex(Exception, "approved"):
            self.run_worker()
        self.assertEqual(self.media.downloads, [])
        self.assertEqual(self.admin.failures[-1], ("INVALID_RENDER_INPUT", True))


    def test_assumed_feature3_image_and_feature5_motion_integrate_without_fallback(self):
        """Assumed input availability exercises contract, NOT real human inference."""
        self.admin.bundle["assets"]["motion01"] = {
            "shop_id": SHOP, "kind": "video", "source_feature": "feature5",
            "approved": True, "storage_bucket": "retailgrowth-media",
            "object_path": SHOP + "/approved/feature5-motion01.mp4",
            "mime_type": "video/mp4", "license_name": "owned",
            "rights_evidence": "Approved fixture provenance for offline contract test",
            "rights_source": "offline mock producer",
        }
        scene = self.admin.bundle["request"]["scenes"][1]
        scene.update({"asset_id": "motion01", "asset_type": "video",
                      "source_feature": "feature5", "motion_status": "ready"})
        self.assertEqual(self.run_worker(), "SUCCEEDED")
        self.assertEqual(len(self.media.downloads), 2)
        self.assertEqual({k.split("/")[-1] for _,k,_ in self.media.downloads},
                         {"product01.png", "feature5-motion01.mp4"})
        self.assertEqual(self.admin.completions[0][-1], "AUTHORIZED_ASSEMBLY")
        self.assertEqual(self.media.uploads[0][-1], LEASE)

    def test_fallback_result_cannot_be_relabelled_as_real_motion(self):
        self.admin.bundle["request"]["allow_image_fallback"] = True
        self.admin.bundle["request"]["scenes"][1].update({
            "asset_id": "motion01", "asset_type": "video", "source_feature": "feature5",
            "motion_status": "failed", "fallback_image_asset_id": "product01",
        })
        def disguised(*args):
            result = fake_render(*args)
            self.assertEqual(result["rendered_as"], "IMAGE_ANIMATION_FALLBACK")
            result["rendered_as"] = "AUTHORIZED_ASSEMBLY"
            return result
        with self.assertRaisesRegex(Feature4HandoffError, "approved input"):
            process_feature4_render(JOB, self.admin, self.media, render_fn=disguised)
        self.assertEqual(self.media.uploads, [])
        self.assertEqual(self.admin.failures[-1], ("INVALID_RENDER_INPUT", True))

    def test_explicitly_approved_image_fallback_keeps_disclosure(self):
        self.admin.bundle["request"]["allow_image_fallback"] = True
        self.admin.bundle["request"]["scenes"][1].update({
            "asset_id": "motion01", "asset_type": "video", "source_feature": "feature5",
            "motion_status": "failed", "fallback_image_asset_id": "product01",
        })
        self.assertEqual(self.run_worker(), "SUCCEEDED")
        self.assertEqual(self.admin.completions[0][-1], "IMAGE_ANIMATION_FALLBACK")

    def test_malformed_or_forged_output_proof_never_uploaded(self):
        examples = (
            ("duration_seconds", 60.0), ("width", 540), ("fps", 30),
            ("video_codec", "mpeg4"), ("audio_codec", "mp3"),
            ("bytes", 999999), ("bytes", True),
            ("sha256", "0" * 64), ("sha256", "garbled"), ("sha256", None),
        )
        for key, value in examples:
            with self.subTest(key=key, value=value):
                self.media = Media()
                self.admin.failures.clear()
                def damaged(*args):
                    result = fake_render(*args)
                    result["output_probe"][key] = value
                    return result
                with self.assertRaises(Feature4HandoffError):
                    process_feature4_render(JOB, self.admin, self.media, render_fn=damaged)
                self.assertEqual(self.media.uploads, [])
                self.assertEqual(self.admin.failures, [("INVALID_RENDER_INPUT", True)])

    def test_renderer_forged_fallback_events_rejected(self):
        def damaged(*args):
            result = fake_render(*args)
            result["fallback_events"] = [{"scene_order": 1, "disclosure": "fictional"}]
            return result
        with self.assertRaisesRegex(Feature4HandoffError, "approved input"):
            process_feature4_render(JOB, self.admin, self.media, render_fn=damaged)
        self.assertEqual(self.media.uploads, [])



if __name__ == "__main__":
    unittest.main()
