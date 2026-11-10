"""Feature4 VoiceStudio original-audio to real compiler contract, offline only."""
import copy
import io
from hashlib import sha256
from pathlib import Path
import sys
import unittest
from uuid import uuid4
import wave

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_voicestudio_handoff import compile_voicestudio_narrated_reel
from creative_contract import CreativeContractError
from test_feature4_intent_compiler import pair


def pcm(seconds=30):
    out=io.BytesIO()
    with wave.open(out,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
        w.writeframes(b"\x02\x01" * (8000*seconds))
    return out.getvalue()


class VoiceStudioHandoffTests(unittest.TestCase):
    def setup_case(self):
        draft, snapshot=pair()
        asset_id=str(uuid4()); request_id=str(uuid4())
        snapshot["assets"][asset_id] = {
            **copy.deepcopy(snapshot["assets"]["musicowned"]),
            "object_path": f"{snapshot['shop_id']}/voicestudio/{snapshot['campaign_id']}/{request_id}/render.wav",
            "mime_type": "audio/wav",
        }
        draft["voiceover_asset_id"]=asset_id
        data=pcm()
        receipt={"shop_id":snapshot["shop_id"],"campaign_id":snapshot["campaign_id"],
                 "audio_asset_id":asset_id,"request_id":request_id,
                 "review_status":"APPROVED_FOR_EDITING","private":True,
                 "rights_reviewed":True,"revoked_at":None,
                 "render_duration_seconds":30,
                 "feature4_audio_sha256":sha256(data).hexdigest()}
        return draft,snapshot,receipt,data

    def call(self,draft,snapshot,receipt,data,*,reader=None):
        return compile_voicestudio_narrated_reel(
            draft=draft,snapshot=snapshot,
            read_current_receipt=reader or (lambda *args:dict(receipt)),
            read_current_private_wav=lambda *args:data,
        )

    def test_real_feature4_compiler_receives_only_approved_private_audio(self):
        draft,snapshot,receipt,data=self.setup_case()
        result=self.call(draft,snapshot,receipt,data)
        aid=draft["voiceover_asset_id"]
        self.assertEqual(result["request"]["voiceover_asset_id"],aid)
        self.assertEqual(result["request"]["voiceover_source"],"retailer")
        self.assertEqual(result["manifest"]["assets"][aid]["shop_id"],snapshot["shop_id"])
        self.assertEqual(result["bundle"]["assets"][aid]["object_path"],
                         snapshot["assets"][aid]["object_path"])
        self.assertNotIn("voiceover_source",draft)

    def test_foreign_and_unapproved_sources_rejected(self):
        mutations=[
            lambda d,s,r: d.update(shop_id=str(uuid4())),
            lambda d,s,r: r.update(shop_id=str(uuid4())),
            lambda d,s,r: r.update(review_status="NEEDS_REVIEW"),
            lambda d,s,r: r.update(rights_reviewed=False),
            lambda d,s,r: r.update(revoked_at="2026-11-11T00:00:00Z"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(shop_id=str(uuid4())),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(approved=False),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(storage_bucket="public"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(object_path="foreign/render.wav"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(license_name="unknown"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(mime_type="audio/mpeg"),
        ]
        for mutate in mutations:
            draft,snapshot,receipt,data=self.setup_case()
            mutate(draft,snapshot,receipt)
            with self.subTest(mutate=mutate),self.assertRaises(CreativeContractError):
                self.call(draft,snapshot,receipt,data)

    def test_bytes_changed_or_timeline_wrong_denied(self):
        d,s,r,data=self.setup_case()
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data[:-10])
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,pcm(15))

    def test_revocation_during_read_is_not_accepted(self):
        d,s,r,data=self.setup_case()
        counts=[0]
        def reader(*_):
            counts[0]+=1
            answer=dict(r)
            if counts[0]>1:answer["revoked_at"]="revoked"
            return answer
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(counts[0],2)

    def test_revocation_after_compilation_is_not_accepted(self):
        d,s,r,data=self.setup_case()
        counts=[0]
        def reader(*_):
            counts[0]+=1
            answer=dict(r)
            if counts[0]>=3:
                answer["review_status"]="REVOKED"
            return answer
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(counts[0],3)

    def test_no_browser_supplied_audio_reader_or_receipt(self):
        d,s,r,data=self.setup_case()
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,read_current_receipt=r,read_current_private_wav=data)

if __name__=="__main__":
    unittest.main()
