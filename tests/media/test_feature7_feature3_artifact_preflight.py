"""Feature7 genuine Feature3 technical media ZIP cross-feature acceptance.

Only actual, exact GitHub artifact 12879355229 can pass the optional
original-source test. Routine CI intentionally lacks that ZIP. Negative
security cases use fake files (never publish or claim video inference).
"""
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from zipfile import ZipFile,ZipInfo

ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from feature3_artifact_preflight import (
    check_feature3_actual_artifact,Feature3ArtifactRejected,EXPECTED,VIDEO_SHA)

ZIP=os.getenv("FEATURE7_F3_ORIGINAL_ARTIFACT_ZIP")

class Feature7Feature3ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.working=tempfile.TemporaryDirectory(prefix="f7-actual-f3-zip-")
        self.addCleanup(self.working.cleanup)
        self.path=Path(self.working.name)/"fixture.zip"

    def test_fake_partial_archive_is_never_valid_customer_or_technical_source(self):
        with ZipFile(self.path,"w") as z:
            z.writestr("feature4-editor-input.mp4",b"fake")
        with self.assertRaises(Feature3ArtifactRejected):
            check_feature3_actual_artifact(str(self.path))

    def test_known_inventory_cannot_contain_symlink(self):
        with ZipFile(self.path,"w") as z:
            for name in EXPECTED:
                info=ZipInfo(name)
                if name=="feature4-editor-input.mp4":
                    info.create_system=3
                    info.external_attr=(stat.S_IFLNK|0o777)<<16
                z.writestr(info,b"TEST_ONLY")
        with self.assertRaises(Feature3ArtifactRejected):
            check_feature3_actual_artifact(str(self.path))

    def test_zip_path_traversal_or_unapproved_extra_file_denied(self):
        for entry in ("../../unowned.mp4","feature5-commercial-output.mp4"):
            with self.subTest(entry=entry):
                with ZipFile(self.path,"w") as z:
                    for name in EXPECTED:z.writestr(name,b"TEST_ONLY")
                    z.writestr(entry,b"untrusted")
                with self.assertRaises(Feature3ArtifactRejected):
                    check_feature3_actual_artifact(str(self.path))

    @unittest.skipUnless(ZIP and shutil.which("ffprobe"),
                         "Original F3 technical Actions ZIP not staged in CI")
    def test_actual_original_feature3_github_artifact_decodes_and_is_unapproved(self):
        report=check_feature3_actual_artifact(str(Path(ZIP).resolve()))
        self.assertEqual(report["feature3_artifact_id"],12879355229)
        self.assertEqual(report["original_video_sha256"],VIDEO_SHA)
        self.assertEqual((report["width"],report["height"]),(1080,1920))
        self.assertEqual(report["duration_seconds"],9.0)
        self.assertTrue(report["feature3_original_file_integrity_verified"])
        self.assertFalse(report["actual_model_try_on_performed"])
        self.assertFalse(report["human_speech_transcribed"])
        self.assertFalse(report["retailer_rights_verified"])
        self.assertFalse(report["publish_approved"])


    @unittest.skipUnless(ZIP and shutil.which("ffprobe"),
                         "Original F3 technical ZIP not staged in CI")
    def test_repacked_unchanged_mp4_but_altered_original_metadata_denied(self):
        # The same original 9s MP4 and images must not mask changes to the
        # embedded manifest, technical source claim or MIT license notice.
        for changed in ("manifest.json","technical_footage_manifest.json",
                        "LICENSE-openvto.txt"):
            with self.subTest(entry=changed):
                with ZipFile(ZIP) as original, ZipFile(self.path,"w") as altered:
                    for info in original.infolist():
                        raw=original.read(info.filename)
                        if info.filename==changed:raw+=b"\\n"
                        altered.writestr(info,raw)
                with self.assertRaisesRegex(Feature3ArtifactRejected,
                                            "pinned Actions ZIP"):
                    check_feature3_actual_artifact(str(self.path))

if __name__=="__main__":
    unittest.main()
