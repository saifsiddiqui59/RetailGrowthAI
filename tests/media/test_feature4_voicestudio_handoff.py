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

    def test_spoofed_voice_provider_or_campaign_denied_before_private_io(self):
        for key, forged in (("voiceover_source", "ai"),
                            ("voiceover_source", "voicestudio-unreviewed"),
                            ("campaign_id", str(uuid4()))):
            draft, snapshot, receipt, data = self.setup_case()
            draft[key] = forged
            calls = []
            def receipt_reader(*args):
                calls.append(args)
                return dict(receipt)
            with self.subTest(key=key, forged=forged), self.assertRaises(CreativeContractError):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=receipt_reader,
                    read_current_private_wav=lambda *_: data)
            self.assertEqual(calls, [], "Invalid scope must not access private media")

    def test_private_narration_rights_metadata_requires_nonblank_strings(self):
        # Truthy numbers, containers and whitespace are not legal evidence.
        for key in ("rights_source", "rights_evidence"):
            for forged in (True, 1, ["unreviewed"], {"claimed": True}, "   ", ""):
                draft, snapshot, receipt, data = self.setup_case()
                snapshot["assets"][draft["voiceover_asset_id"]][key] = forged
                with self.subTest(key=key, forged=forged), self.assertRaises(CreativeContractError):
                    self.call(draft, snapshot, receipt, data)

    def test_malformed_trusted_media_manifest_fails_closed(self):
        for invalid in (None, [], "not-a-manifest", 7):
            d,s,r,data=self.setup_case()
            s["assets"]=invalid
            with self.subTest(invalid=invalid), self.assertRaises(CreativeContractError):
                self.call(d,s,r,data)

    def test_trusted_receipt_type_confusion_denied(self):
        # Python considers True == 1, but durable approval must be boolean.
        for key, forged in (
            ("private", 1), ("rights_reviewed", 1),
            ("render_duration_seconds", 30.0),
            ("revoked_at", False),
        ):
            draft, snapshot, receipt, data = self.setup_case()
            receipt[key] = forged
            with self.subTest(key=key), self.assertRaises(CreativeContractError):
                self.call(draft, snapshot, receipt, data)

    def test_bytes_changed_or_timeline_wrong_denied(self):
        d,s,r,data=self.setup_case()
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data[:-10])
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,pcm(15))

    def test_private_wav_rejects_trailing_bytes_and_forged_riff_size(self):
        # The digest can match a malformed private object; container framing
        # must independently reject bytes that wave.open silently ignores.
        for mutate in (
            lambda raw: raw + b"untrusted trailing bytes",
            lambda raw: raw[:4] + (len(raw) - 9).to_bytes(4, "little") + raw[8:],
            lambda raw: b"RIFX" + raw[4:],
        ):
            d,s,r,data=self.setup_case()
            malformed=mutate(data)
            r["feature4_audio_sha256"]=sha256(malformed).hexdigest()
            with self.subTest(mutate=mutate), self.assertRaises(CreativeContractError):
                self.call(d,s,r,malformed)

    def test_private_wav_rejects_hidden_riff_chunks(self):
        # A correct outer RIFF length is insufficient: wave.open ignores
        # unknown chunks after data, duplicate data and trailing bytes.
        for extra in (b"JUNK" + (4).to_bytes(4, "little") + b"evil",
                      b"data" + (2).to_bytes(4, "little") + b"xx",
                      b"JUNK" + (5).to_bytes(4, "little") + b"short"):
            d, s, r, data = self.setup_case()
            forged = data + extra
            forged = forged[:4] + (len(forged) - 8).to_bytes(4, "little") + forged[8:]
            r["feature4_audio_sha256"] = sha256(forged).hexdigest()
            with self.subTest(extra=extra), self.assertRaises(CreativeContractError):
                self.call(d, s, r, forged)

    def test_private_wav_rejects_empty_data_and_nonzero_padding(self):
        # Even a receipt whose digest matches cannot authorize ambiguous PCM.
        d, s, r, data = self.setup_case()
        empty = data[:40] + (0).to_bytes(4, "little")
        empty = empty[:4] + (len(empty) - 8).to_bytes(4, "little") + empty[8:]
        r["feature4_audio_sha256"] = sha256(empty).hexdigest()
        with self.assertRaises(CreativeContractError):
            self.call(d, s, r, empty)

        # A nonzero odd-chunk padding byte is not a canonical WAV object.
        d, s, r, data = self.setup_case()
        # Append an odd data payload and its deliberately nonzero pad byte.
        odd = data[:40] + (len(data) - 44 + 1).to_bytes(4, "little") + data[44:] + b"\x01\xff"
        odd = odd[:4] + (len(odd) - 8).to_bytes(4, "little") + odd[8:]
        r["feature4_audio_sha256"] = sha256(odd).hexdigest()
        with self.assertRaises(CreativeContractError):
            self.call(d, s, r, odd)

    def test_private_wav_rejects_inconsistent_pcm_headers_and_partial_frames(self):
        # Valid SHA and RIFF length do not make a forged PCM layout safe.
        for offset, width, value in (
            (22, 2, 1),        # 8-bit samples but 16-bit frame data
            (32, 2, 1),        # block alignment disagrees with channels
            (28, 4, 1),        # byte rate disagrees with sample rate
            (24, 4, 0),        # invalid sample rate
            (22, 2, 24),       # unsupported 24-bit PCM
        ):
            d, s, r, data = self.setup_case()
            forged = data[:offset] + value.to_bytes(width, "little") + data[offset + width:]
            r["feature4_audio_sha256"] = sha256(forged).hexdigest()
            with self.subTest(offset=offset, value=value), self.assertRaises(CreativeContractError):
                self.call(d, s, r, forged)

        d, s, r, data = self.setup_case()
        # Add one unaligned PCM byte and a legal zero RIFF padding byte.
        payload = data[:40] + (len(data) - 44 + 1).to_bytes(4, "little") + data[44:] + b"\\x01\\x00"
        payload = payload[:4] + (len(payload) - 8).to_bytes(4, "little") + payload[8:]
        r["feature4_audio_sha256"] = sha256(payload).hexdigest()
        with self.assertRaises(CreativeContractError):
            self.call(d, s, r, payload)

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

    def test_in_place_receipt_revocation_during_read_denied(self):
        # A trusted service reader can return the same mutable cached dict.
        # An aliased baseline must never hide a post-read approval change.
        d,s,r,data=self.setup_case()
        calls=[0]
        def reader(*_):
            calls[0]+=1
            if calls[0]==2:
                r["review_status"]="REVOKED"
            return r
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(calls[0],2)

    def test_in_place_receipt_revocation_during_compile_denied(self):
        d,s,r,data=self.setup_case()
        calls=[0]
        def reader(*_):
            calls[0]+=1
            if calls[0]==3:
                r["revoked_at"]="2026-11-11T00:00:00Z"
            return r
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(calls[0],3)

    def test_private_media_replacement_during_read_denied(self):
        d,s,r,data=self.setup_case()
        asset=d["voiceover_asset_id"]
        def private_reader(*_):
            s["assets"][asset]["object_path"]="other-tenant/forged.wav"
            return data
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,
                read_current_receipt=lambda *_:dict(r),
                read_current_private_wav=private_reader)

    def test_private_media_replacement_during_compile_denied(self):
        d,s,r,data=self.setup_case()
        asset=d["voiceover_asset_id"]
        reads=[0]
        def receipt_reader(*_):
            reads[0]+=1
            if reads[0]==3:
                s["assets"][asset]["rights_evidence"]="replaced-during-compile"
            return dict(r)
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,
                read_current_receipt=receipt_reader,
                read_current_private_wav=lambda *_:data)
        self.assertEqual(reads[0],3)

    def test_private_bytes_replaced_during_compilation_denied(self):
        d,s,r,data=self.setup_case()
        calls=[0]
        def private_reader(*_):
            calls[0]+=1
            return data if calls[0]==1 else data[:-2]+b"\x00\x00"
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,
                read_current_receipt=lambda *_:dict(r),
                read_current_private_wav=private_reader)
        self.assertEqual(calls[0],2)

    def test_revocation_after_final_private_read_denied(self):
        d,s,r,data=self.setup_case()
        calls=[0]
        def reader(*_):
            calls[0]+=1
            answer=dict(r)
            if calls[0]>=4:answer["review_status"]="REVOKED"
            return answer
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(calls[0],4)

    def test_no_browser_supplied_audio_reader_or_receipt(self):
        d,s,r,data=self.setup_case()
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,read_current_receipt=r,read_current_private_wav=data)

if __name__=="__main__":
    unittest.main()
