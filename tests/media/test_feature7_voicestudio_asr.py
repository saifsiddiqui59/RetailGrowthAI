"""Feature7 VoiceStudio API contract: no ASR weights, cloud or video render."""
import io
import json
from hashlib import sha256
from pathlib import Path
import sys
import unittest
import wave

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from voicestudio_transcription import (VoiceStudioTranscriptionDenied,
                                       transcribe_private_voice)


def wav():
    out=io.BytesIO()
    with wave.open(out,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(b"\x02\x01" * 32000)
    return out.getvalue()


class Reply(io.BytesIO):
    status=200
    headers={"Content-Type":"application/json"}
    def __init__(self,body,**kwargs):
        super().__init__(body)
        self.url=kwargs.get("url","http://127.0.0.1:3900/v1/audio/transcriptions")
        self.status=kwargs.get("status",200)
        self.headers={"Content-Type":kwargs.get("mime","application/json")}
    def geturl(self): return self.url


class TestVoiceStudioSpeechReview(unittest.TestCase):
    def setUp(self):
        self.original=wav()
        self.calls=[]
        self.payload={
            "task":"transcribe","language":"hi","duration":2.0,
            "text":"नमस्ते दुनिया",
            "words":[{"start":0.1,"end":0.7,"word":"नमस्ते"},
                     {"start":0.8,"end":1.5,"word":"दुनिया"}],
        }

    def sender(self,req,timeout):
        self.calls.append((req,timeout))
        return Reply(json.dumps(self.payload,ensure_ascii=False).encode())

    def call(self,**options):
        params={
            "original_wav":self.original,
            "source_sha256":sha256(self.original).hexdigest(),
            "base_url":"http://127.0.0.1:3900",
            "api_key":"only-a-placeholder-123456789",
            "language":"hi","enabled":True,
            "commercial_model_verified":True,
            "transport":self.sender,
        }
        params.update(options)
        return transcribe_private_voice(**params)

    def test_word_level_upstream_contract_retains_indic_text(self):
        result=self.call()
        self.assertEqual(result["language"],"hi")
        self.assertEqual(result["words"][0]["word"],"नमस्ते")
        self.assertEqual(result["text"],"नमस्ते दुनिया")
        self.assertFalse(result["approved"])
        self.assertFalse(result["renderable"])
        self.assertTrue(result["requires_feature7_signed_evidence"])
        self.assertEqual(len(self.calls),1)
        req,timeout=self.calls[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(timeout,60)
        self.assertEqual(req.full_url,"http://127.0.0.1:3900/v1/audio/transcriptions")
        self.assertIn(b'name="response_format"',req.data)
        self.assertIn(b"verbose_json",req.data)
        self.assertIn(b'timestamp_granularities[]',req.data)
        self.assertIn(self.original,req.data)

    def test_none_of_the_denied_requests_egress(self):
        examples=[
            {"enabled":False},
            {"commercial_model_verified":False},
            {"api_key":"short"},
            {"source_sha256":"0"*64},
            {"base_url":"http://public.example:3900"},
            {"base_url":"http://127.0.0.1:3900@evil.test:3900"},
            {"base_url":"file:///etc/passwd"},
            {"language":"unknown"},
            {"original_wav":b"fake WAV"},
        ]
        for case in examples:
            with self.subTest(case=case):
                self.calls.clear()
                with self.assertRaises(VoiceStudioTranscriptionDenied):
                    self.call(**case)
                self.assertEqual(self.calls,[])

    def test_missing_or_invalid_word_timing_fails_closed(self):
        bad=[
            None, [],
            [{"start":0.1,"end":0.2,"word":""}],
            [{"start":1.1,"end":0.9,"word":"late"}],
            [{"start":0.1,"end":3.0,"word":"overrun"}],
            [{"start":0.1,"end":0.5,"word":"first"},
             {"start":0.4,"end":0.6,"word":"overlap"}],
            [{"start":True,"end":0.6,"word":"bool"}],
            [{"start":float("nan"),"end":0.6,"word":"nan"}],
        ]
        for words in bad:
            self.payload["words"]=words
            with self.subTest(words=words),self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call()

    def test_canonical_millisecond_timing_and_unicode_fail_closed(self):
        # Upstream timings may be valid floats but invalid after receipt
        # canonicalization. Never sign zero-length or overlapping words.
        invalid = [
            [{"start":0.1001,"end":0.1004,"word":"tiny"}],
            [{"start":0.1001,"end":0.1006,"word":"first"},
             {"start":0.1007,"end":0.1012,"word":"second"}],
            [{"start":0.1,"end":0.7,"word":"\\ud800"}],
        ]
        for words in invalid:
            self.payload["words"] = words
            with self.subTest(words=words), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call()
        self.payload["words"] = [
            {"start":0.1001,"end":0.7001,"word":"नमस्ते"},
            {"start":0.8001,"end":1.5001,"word":"दुनिया"},
        ]
        result = self.call()
        self.assertEqual(result["words"][0],
                         {"start":0.1,"end":0.7,"word":"नमस्ते"})

    def test_upstream_status_url_and_mime_are_verified(self):
        for conf in [{"status":202},{"url":"https://evil.test/"},{"mime":"text/html"}]:
            def sender(req,timeout):
                return Reply(json.dumps(self.payload).encode(),**conf)
            with self.subTest(conf=conf),self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(transport=sender)

    def test_malformed_large_payload_and_wrong_task_denied(self):
        for payload in [b"x", b"x" * (512*1024+1), b"[]",
                        b'{"task":"translate"}']:
            with self.subTest(n=len(payload)),self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(transport=lambda req,timeout:Reply(payload))

    def test_upstream_error_redacted(self):
        from urllib.error import URLError
        def sender(req,timeout):
            raise URLError("secret should not be returned")
        with self.assertRaises(VoiceStudioTranscriptionDenied) as e:
            self.call(transport=sender)
        self.assertNotIn("secret",str(e.exception))


if __name__=="__main__":
    unittest.main()
