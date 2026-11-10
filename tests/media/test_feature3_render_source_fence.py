"""Offline safety checks for v2 render source / explicit two-digest binding."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from versioned_source_v2 import bind_authorized_versioned_design, Feature3SourceDenied

class TestFeature3RenderSourceFence(unittest.TestCase):
    def setUp(self):
        self.sid,self.did=[str(uuid4()) for _ in range(2)]
        self.sha="a"*64
        self.design={"schema":"retailgrowth.poster.v2","shop_id":self.sid,
             "format":"square","template":"fashion","background":"#FFFFFF",
             "layers":[{"id":"brand","type":"text","x":0.1,"y":0.2,"w":0.8,"h":0.2,
                        "text":"RetailGrowthAI","color":"#222222","font_size":35,"bold":True}]}
        self.row={"id":self.did,"shop_id":self.sid,"revision":2,"status":"DRAFT",
                  "server_document_sha256":self.sha,"design":self.design}
        self.calls=[]
    def read(self,sid,did,revision,digest):
        self.calls.append((sid,did,revision,digest))
        return self.row
    def allow(self,sid,assets,row):
        return sid==self.sid and assets==() and row is self.row
    def bind(self,**overrides):
        args={"shop_id":self.sid,"design_id":self.did,"expected_revision":2,
              "expected_server_sha256":self.sha,"read_version_under_lock":self.read,
              "authorize_current_images":self.allow}
        args.update(overrides)
        return bind_authorized_versioned_design(**args)

    def test_authorized_draft_has_both_distinct_hash_receipts_without_queue_or_spend(self):
        out=self.bind()
        self.assertEqual(out["revision"],2)
        self.assertEqual(out["server_document_sha256"],self.sha)
        self.assertRegex(out["design_sha256"],r"^[a-f0-9]{64}$")
        self.assertNotEqual(out["design_sha256"],self.sha)
        self.assertFalse(out["ready_for_queue"])
        self.assertFalse(out["usage_reserved"])
        self.assertFalse(out["rendered"])
        self.assertFalse(out["signed_output"])
        self.assertEqual(self.calls,[(self.sid,self.did,2,self.sha)])
    def test_reject_foreign_shop_stale_revision_changed_hash_and_approval(self):
        for mutate in (
            {"shop_id":str(uuid4())},
            {"revision":3},
            {"status":"APPROVED"},
            {"server_document_sha256":"b"*64},
            {"id":str(uuid4())},
        ):
            original=self.row
            self.row={**original,**mutate}
            with self.assertRaises(Feature3SourceDenied):self.bind()
            self.row=original
    def test_reject_replaced_or_revoked_media_and_forged_browser_record(self):
        self.design["layers"].append({"id":"product","type":"image",
            "asset_id":str(uuid4()),"x":0.1,"y":0.45,"w":0.8,"h":0.4})
        with self.assertRaises(Feature3SourceDenied):self.bind()
        with self.assertRaises(Feature3SourceDenied):self.bind(authorize_current_images=None)
        with self.assertRaises(Feature3SourceDenied):self.bind(read_version_under_lock=lambda *a: {"status":"DRAFT"})
    def test_reject_noncanonical_uuid_invalid_revision_and_bad_digest(self):
        for kw in ({"shop_id":"../foo"},{"design_id":"not-a-uuid"},
                   {"expected_revision":True},{"expected_revision":0},
                   {"expected_server_sha256":"0"*63}):
            with self.assertRaises(Feature3SourceDenied):self.bind(**kw)

if __name__=="__main__":unittest.main()
