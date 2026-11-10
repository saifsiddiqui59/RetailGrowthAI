"""Offline synthetic fixtures: actual OpenPeople pixels/rights are NOT tested."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'poster-engine'))
from model_library_v2 import ModelLibraryDenied
from openpeople_indian_review_v2 import expected_review_packet
import openpeople_pilot_qa_v2 as pilot


class PrivatePilotReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        image = Image.new('RGB', (400, 650), '#9bafc0')
        buffer = io.BytesIO()
        image.save(buffer, 'JPEG')
        self.synthetic_jpg = buffer.getvalue()
        self.packet = expected_review_packet('P009', 'studio_posture')
        self.json_packet = json.dumps(self.packet)

    def test_private_unapproved_visual_contact_sheet_and_provenance(self):
        out = self.root / 'source-review'
        with patch.object(pilot, 'read_verified_still', return_value=self.synthetic_jpg) as read:
            record = pilot.build_private_pilot_review(
                [self.json_packet], dataset_root=self.root, output_dir=out)
        read.assert_called_once()
        self.assertEqual(record['status'], 'UNAPPROVED_PRIVATE_REVIEW_ONLY')
        self.assertFalse(record['commercial_rights_cleared'])
        self.assertFalse(record['ready_for_cloud_import'])
        self.assertEqual(record['generation_gpu_calls'], 0)
        self.assertFalse(record['source_assets'][0]['eligible_for_library_import'])
        self.assertEqual(record['source_assets'][0]['source_width'], 400)
        with Image.open(out / 'pilot-contact-sheet-UNAPPROVED.png') as image:
            self.assertEqual(image.size, (400, 450))
        on_disk = json.loads((out / 'pilot-review-UNAPPROVED.json').read_text())
        self.assertEqual(on_disk, record)
        if os.name == 'posix':
            self.assertEqual(out.stat().st_mode & 0o777, 0o700)
            for name in ('pilot-contact-sheet-UNAPPROVED.png', 'pilot-review-UNAPPROVED.json'):
                self.assertEqual((out / name).stat().st_mode & 0o777, 0o600)

    def test_forged_approval_and_extra_packet_fields_never_trigger_source_read(self):
        for changed in ({**self.packet, 'approved': True},
                        {**self.packet, 'licensed_for_retailgrowth': True},
                        {**self.packet, 'hidden_license_grant': True},
                        {**self.packet, 'image_git_blob_sha': '0'*40}):
            with self.subTest(changed=changed):
                with patch.object(pilot, 'read_verified_still') as read:
                    with self.assertRaises(ModelLibraryDenied):
                        pilot.build_private_pilot_review(
                            [json.dumps(changed)], dataset_root=self.root,
                            output_dir=self.root / 'no-output')
                    read.assert_not_called()
                self.assertFalse((self.root / 'no-output').exists())

    def test_missing_real_jpg_does_not_produce_fake_genuine_pilot(self):
        with self.assertRaises(ModelLibraryDenied):
            pilot.build_private_pilot_review(
                [self.json_packet], dataset_root=self.root,
                output_dir=self.root / 'missing-source')
        self.assertFalse((self.root / 'missing-source').exists())

    def test_duplicate_and_unbounded_pilot_rejected(self):
        with patch.object(pilot, 'read_verified_still', return_value=self.synthetic_jpg):
            with self.assertRaisesRegex(ModelLibraryDenied, 'Duplicate'):
                pilot.build_private_pilot_review(
                    [self.json_packet, self.json_packet],
                    dataset_root=self.root, output_dir=self.root / 'repeat')
            with self.assertRaisesRegex(ModelLibraryDenied, 'at most three'):
                pilot.build_private_pilot_review(
                    [self.json_packet]*4, dataset_root=self.root,
                    output_dir=self.root / 'too-many')
        self.assertFalse((self.root / 'repeat').exists())

    def test_source_allowlist_denies_fake_sha_even_if_image_exists(self):
        from openpeople_import_v2 import OpenPeopleSelection
        invalid = OpenPeopleSelection(
            dataset_root=self.root,
            source_revision=self.packet['source_revision'],
            person_id='P009', image_kind='studio_posture',
            expected_image_git_blob_sha='0'*40)
        with self.assertRaisesRegex(ModelLibraryDenied, 'immutable pilot allowlist'):
            pilot.read_verified_still(invalid)

    def test_exact_catalog_selection_denies_substituted_real_path_bytes(self):
        from openpeople_indian_review_v2 import parse_review_packet_file
        selection = parse_review_packet_file(self.json_packet, dataset_root=self.root)
        path = (self.root / 'openpeople/data/curated/P009/assets/studio_posture.jpg')
        path.parent.mkdir(parents=True)
        path.write_bytes(self.synthetic_jpg)
        with self.assertRaisesRegex(ModelLibraryDenied, 'does not match pinned'):
            pilot.read_verified_still(selection)

    def test_symlinked_upstream_image_is_never_read(self):
        from openpeople_indian_review_v2 import parse_review_packet_file
        selection = parse_review_packet_file(self.json_packet, dataset_root=self.root)
        path = (self.root / 'openpeople/data/curated/P009/assets/studio_posture.jpg')
        path.parent.mkdir(parents=True)
        raw = self.root / 'other-person.jpg'
        raw.write_bytes(self.synthetic_jpg)
        try:
            path.symlink_to(raw)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        with self.assertRaisesRegex(ModelLibraryDenied, 'Symlinked'):
            pilot.read_verified_still(selection)

    def test_output_reuse_refused_without_overwriting(self):
        out = self.root / 'source-review'
        with patch.object(pilot, 'read_verified_still', return_value=self.synthetic_jpg):
            pilot.build_private_pilot_review(
                [self.json_packet], dataset_root=self.root, output_dir=out)
            before = (out / 'pilot-review-UNAPPROVED.json').read_bytes()
            with self.assertRaisesRegex(ModelLibraryDenied, 'do not overwrite'):
                pilot.build_private_pilot_review(
                    [self.json_packet], dataset_root=self.root, output_dir=out)
            self.assertEqual(before, (out / 'pilot-review-UNAPPROVED.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
