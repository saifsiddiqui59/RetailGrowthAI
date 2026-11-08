"""F3-08 synthetic binding tests: never evidence of hosted authorization."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_rights_binding import build_private_png_reader, build_scoped_private_png_reader


class Store:
    origin = "https://example.supabase.co"
    key = "sb_publishable_abcdef123456"
    def member(self, *args): return True
    def feature3_gpu_job(self, *args): return None
    def feature3_generated_asset(self, *args): return None


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset = [str(uuid4()) for _ in range(3)]
        self.calls = 0
        self.row = dict(
            shop_id=self.shop, job_id=self.job, asset_id=self.asset,
            output_sha256="a" * 64, rights_revision=2,
            output_registered=True, source_rights_current=True,
            customer_approval_current=True, rights_revoked=False,
            job_succeeded=True, private_storage=True,
        )

    def authority(self, *args):
        self.calls += 1
        return dict(self.row)

    def build(self, **changes):
        values = dict(tenant_store=Store(), verify_user_jwt=lambda token: self.shop,
                      authoritative_read=self.authority,
                      expected_output_sha256="a" * 64,
                      minimum_rights_revision=2)
        values.update(changes)
        return build_private_png_reader(**values)

    def test_binding_rechecks_current_authority_and_revocation(self):
        reader = self.build()
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.row["rights_revoked"] = True
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 2)

    def test_binding_denies_foreign_shop_and_stale_revision(self):
        reader = self.build()
        self.assertFalse(reader.rights(str(uuid4()), self.job, self.asset))
        self.row["rights_revision"] = 1
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))

    def test_binding_denies_substituted_digest(self):
        reader = self.build()
        self.row["output_sha256"] = "b" * 64
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))

    def test_malformed_trusted_pins_never_construct_reader(self):
        bad_digests = ("A" * 64, "a" * 63, "a" * 65, "", 123, True, [], {})
        for digest in bad_digests:
            with self.subTest(digest=repr(digest)):
                with self.assertRaises(ValueError):
                    self.build(expected_output_sha256=digest)
        for revision in (0, -1, True, 1.0, "2", [], {}):
            with self.subTest(revision=repr(revision)):
                with self.assertRaises(ValueError):
                    self.build(minimum_rights_revision=revision)
        self.assertEqual(self.calls, 0)

    def test_new_rights_revision_must_still_recheck_revocation_and_digest(self):
        reader = self.build()
        self.row["rights_revision"] = 3
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.row["source_rights_current"] = False
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.row["source_rights_current"] = True
        self.row["output_sha256"] = "b" * 64
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 3)

    def test_missing_trusted_pins_fail_before_reader_construction(self):
        for changes in (dict(expected_output_sha256=None),
                        dict(minimum_rights_revision=None),
                        dict(authoritative_read=None),
                        dict(verify_user_jwt=None)):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.build(**changes)
        self.assertEqual(self.calls, 0)


    def test_scoped_pins_authorize_only_matching_output(self):
        calls = []
        def pins(shop, job):
            calls.append((shop, job))
            return dict(shop_id=shop, job_id=job,
                        output_sha256="a" * 64, rights_revision=2)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority, trusted_output_pins=pins)
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(calls, [(self.shop, self.job)] * 3)
        self.assertFalse(reader.rights(str(uuid4()), self.job, self.asset))

    def test_scoped_reader_never_reuses_pins_for_another_job(self):
        foreign_job = str(uuid4())
        foreign_shop = str(uuid4())
        observed = []
        def backend(shop, job, asset):
            observed.append((shop, job, asset))
            # Simulate another output with the same digest and rights revision.
            return dict(self.row, shop_id=shop, job_id=job, asset_id=asset)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=backend,
            trusted_output_pins=lambda shop, job: dict(
                shop_id=shop, job_id=job,
                output_sha256="a" * 64, rights_revision=2),
        )
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.assertFalse(reader.rights(self.shop, foreign_job, self.asset))
        self.assertFalse(reader.rights(foreign_shop, self.job, self.asset))
        self.assertEqual(observed, [(self.shop, self.job, self.asset)])

    def test_scoped_reader_denies_changed_pins_and_recovers(self):
        snapshot = dict(shop_id=self.shop, job_id=self.job,
                        output_sha256="a" * 64, rights_revision=2)
        pin_calls = []
        def pins(shop, job):
            pin_calls.append((shop, job))
            return dict(snapshot)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority, trusted_output_pins=pins)
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        snapshot["rights_revision"] = 3
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        snapshot["rights_revision"] = 2
        snapshot["output_sha256"] = "b" * 64
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        snapshot["output_sha256"] = "a" * 64
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 2)
        self.assertEqual(len(pin_calls), 7)

    def test_scoped_reader_denies_malformed_pin_refresh(self):
        snapshot = dict(shop_id=self.shop, job_id=self.job,
                        output_sha256="a" * 64, rights_revision=2)
        def pins(shop, job):
            return dict(snapshot)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority, trusted_output_pins=pins)
        snapshot["rights_revision"] = True
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        snapshot["rights_revision"] = 2
        snapshot["shop_id"] = str(uuid4())
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 0)

    def test_scoped_reader_rejects_missing_backend_callback(self):
        with self.assertRaises(ValueError):
            build_scoped_private_png_reader(
                shop_id=self.shop, job_id=self.job, tenant_store=Store(),
                verify_user_jwt=lambda token: self.shop,
                authoritative_read=None,
                trusted_output_pins=lambda shop, job: dict(
                    shop_id=shop, job_id=job,
                    output_sha256="a" * 64, rights_revision=2),
            )

    def test_scoped_pins_reject_cross_shop_and_malformed_authority(self):
        good = dict(shop_id=self.shop, job_id=self.job,
                    output_sha256="a" * 64, rights_revision=2)
        def attempt(callback, shop=None, job=None):
            return build_scoped_private_png_reader(
                shop_id=self.shop if shop is None else shop,
                job_id=self.job if job is None else job,
                tenant_store=Store(), verify_user_jwt=lambda token: self.shop,
                authoritative_read=self.authority,
                trusted_output_pins=callback)
        bad = [
            dict(good, shop_id=str(uuid4())),
            dict(good, job_id=str(uuid4())),
            dict(good, output_sha256="b" * 63),
            dict(good, rights_revision=True),
            dict(good, extra=True),
            {k: v for k, v in good.items() if k != "rights_revision"},
            None, [], True,
        ]
        for row in bad:
            with self.subTest(row=repr(row)):
                with self.assertRaises(ValueError):
                    attempt(lambda shop, job, value=row: value)
        with self.assertRaises(ValueError):
            attempt(lambda shop, job: (_ for _ in ()).throw(RuntimeError("backend down")))
        with self.assertRaises(ValueError):
            attempt(lambda shop, job: good, shop="not-a-uuid")
        self.assertEqual(self.calls, 0)


    def test_scoped_authority_rejects_overloaded_equality_objects(self):
        class Spoof:
            def __eq__(self, other):
                return True

        observed = []
        def backend(shop, job, asset):
            observed.append((shop, job, asset))
            return dict(self.row)

        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=backend,
            trusted_output_pins=lambda shop, job: dict(
                shop_id=shop, job_id=job,
                output_sha256="a" * 64, rights_revision=2),
        )
        for request in ((Spoof(), self.job, self.asset),
                        (self.shop, Spoof(), self.asset),
                        (self.shop, self.job, Spoof())):
            with self.subTest(request=request):
                self.assertFalse(reader.rights(*request))
        self.assertEqual(observed, [])
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(observed, [(self.shop, self.job, self.asset)])



    def test_scoped_binding_module_is_valid_python_source(self):
        # Regression for escaped newline text inserted into a Python comment.
        source_path = (Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api" /
                       "feature3_private_rights_binding.py")
        source = source_path.read_text(encoding="utf-8")
        compile(source, str(source_path), "exec")
        self.assertIn("pins = dict(pins)", source)

    def test_scoped_binding_rejects_noncanonical_scope_before_pin_lookup(self):
        calls = []
        def pins(shop, job):
            calls.append((shop, job))
            return dict(shop_id=shop, job_id=job,
                        output_sha256="a" * 64, rights_revision=2)
        for bad_shop, bad_job in ((self.shop.upper(), self.job),
                                  (self.shop, self.job.upper()),
                                  (self.shop, "not-a-uuid")):
            with self.subTest(shop=bad_shop, job=bad_job):
                with self.assertRaises(ValueError):
                    build_scoped_private_png_reader(
                        shop_id=bad_shop, job_id=bad_job,
                        tenant_store=Store(),
                        verify_user_jwt=lambda token: self.shop,
                        authoritative_read=self.authority,
                        trusted_output_pins=pins)
        self.assertEqual(calls, [])
        self.assertEqual(self.calls, 0)

    def test_scoped_reader_freezes_mutable_backend_pin_object(self):
        # A real adapter can reuse one mutable row object between calls.
        # Mutation must not rewrite the initial trust baseline in place.
        shared = dict(shop_id=self.shop, job_id=self.job,
                      output_sha256="a" * 64, rights_revision=2)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority,
            trusted_output_pins=lambda shop, job: shared)
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        shared["rights_revision"] = 3
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        shared["rights_revision"] = 2
        shared["output_sha256"] = "b" * 64
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        shared["output_sha256"] = "a" * 64
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 2)

    def test_scoped_reader_denies_pin_change_during_authority_lookup(self):
        # Synthetic race: output is replaced after the first pin check but
        # before the authority returns an otherwise valid approval receipt.
        pins_row = dict(shop_id=self.shop, job_id=self.job,
                        output_sha256="a" * 64, rights_revision=2)
        def pins(shop, job):
            return dict(pins_row)
        def racing_authority(shop, job, asset):
            pins_row["rights_revision"] = 3
            return dict(self.row)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=racing_authority, trusted_output_pins=pins)
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        # A stable current snapshot can be accepted again, but the
        # intervening stale approval must never be returned.
        pins_row["rights_revision"] = 2
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 0)

    def test_scoped_reader_denies_pin_refresh_outage_after_authority(self):
        state = {"calls": 0}
        def pins(shop, job):
            state["calls"] += 1
            if state["calls"] == 3:
                raise OSError("synthetic second pin read failed")
            return dict(shop_id=shop, job_id=job,
                        output_sha256="a" * 64, rights_revision=2)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority, trusted_output_pins=pins)
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 1)

    def test_scoped_reader_denies_pin_lookup_outage_after_construction(self):
        state = {"available": True}
        def pins(shop, job):
            if not state["available"]:
                raise OSError("synthetic backend outage")
            return dict(shop_id=shop, job_id=job,
                        output_sha256="a" * 64, rights_revision=2)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority, trusted_output_pins=pins)
        state["available"] = False
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 0)
        state["available"] = True
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 1)

    def test_scoped_reader_denies_pin_scope_change_without_authority_call(self):
        state = {"shop": self.shop}
        def pins(shop, job):
            return dict(shop_id=state["shop"], job_id=job,
                        output_sha256="a" * 64, rights_revision=2)
        reader = build_scoped_private_png_reader(
            shop_id=self.shop, job_id=self.job, tenant_store=Store(),
            verify_user_jwt=lambda token: self.shop,
            authoritative_read=self.authority, trusted_output_pins=pins)
        state["shop"] = str(uuid4())
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 0)

if __name__ == "__main__":
    unittest.main()
