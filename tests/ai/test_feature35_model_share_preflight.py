"""CPU-only tests; no Azure login, no model bytes, no GPU."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from scripts.ops import feature35_model_share_preflight as m


def original_manifest():
    return {"gpu_started":False,"total_bytes":m.TOTAL,
            "files":[{"path":p,"size":sz,"sha256":sha,"source":src,"revision":"1"*40}
                     for p,(sz,sha,src) in m.BY_PATH.items()]}


class TestReadOnlyModelAudit(unittest.TestCase):
    def setUp(self):
        self.doc=original_manifest()

    def test_exact_six_files_upstream_and_bytes(self):
        paths,rev=m.check_manifest(self.doc)
        self.assertEqual(len(paths),6)
        self.assertEqual(len(rev),3)
        self.assertEqual(sum(p["size"] for p in paths.values()),34277265757)

    def test_bad_metadata_never_accepted(self):
        for k,v in [("sha256","f"*64),("size",1),("source","unknown/repo"),("revision","main")]:
            d=original_manifest()
            d["files"][0][k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):
                m.check_manifest(d)
        d=original_manifest()
        d["files"][-1]=d["files"][0].copy()
        with self.assertRaises(ValueError):m.check_manifest(d)
        d=original_manifest()
        d["gpu_started"]=True
        with self.assertRaises(ValueError):m.check_manifest(d)

    def test_mismatched_revision_denied(self):
        d=original_manifest()
        d["files"][1]["revision"]="2"*40
        with self.assertRaises(ValueError):m.check_manifest(d)

    def test_audit_gets_only_tiny_json_no_weight_bodies(self):
        d=json.dumps(self.doc).encode()
        share=Mock()
        share.get_share_properties.return_value=SimpleNamespace(access_tier="Cool",quota=64)
        marker=Mock()
        marker.get_file_properties.return_value=SimpleNamespace(size=len(d))
        marker.download_file.return_value.readall.return_value=d
        model_clients={}
        for row in self.doc["files"]:
            file=Mock()
            file.get_file_properties.return_value=SimpleNamespace(
                size=row["size"],metadata={"complete":"true","sha256":row["sha256"],"revision":row["revision"]})
            model_clients[row["path"]]=file
        share.get_file_client.side_effect=lambda path: marker if path=="models-sha256-manifest.json" else model_clients[path]
        report=m.check_share(share)
        self.assertEqual(report["verified_files"],6)
        self.assertFalse(report["model_bodies_rehashed"])
        for client in model_clients.values():client.download_file.assert_not_called()

    def test_oversized_manifest_denied_before_download(self):
        share=Mock()
        share.get_share_properties.return_value=SimpleNamespace(access_tier="Cool",quota=64)
        marker=share.get_file_client.return_value
        marker.get_file_properties.return_value=SimpleNamespace(size=70000)
        with self.assertRaises(ValueError):m.check_share(share)
        marker.download_file.assert_not_called()
