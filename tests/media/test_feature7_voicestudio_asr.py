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

    def test_riff_declared_length_mismatch_denied_without_egress(self):
        # A valid WAV decoder may ignore trailing bytes or RIFF size tampering.
        # Never send those noncanonical original bytes to the ASR endpoint.
        cases = [self.original + b"extra",
                 self.original[:-2],
                 self.original[:4] + (len(self.original) - 9).to_bytes(4, "little") + self.original[8:]]
        for malformed in cases:
            self.calls.clear()
            with self.subTest(length=len(malformed)), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(original_wav=malformed,
                          source_sha256=sha256(malformed).hexdigest())
            self.assertEqual(self.calls, [])

    def test_ambiguous_riff_chunks_denied_before_asr_egress(self):
        # wave.open accepts valid PCM followed by extra chunks; downstream
        # evidence signing must not disagree with upstream ASR input validity.
        original = self.original
        extra = b"JUNK" + (0).to_bytes(4, "little")
        duplicate_data = b"data" + (2).to_bytes(4, "little") + b"\\x00\\x00"
        duplicate_fmt = original[12:36]
        layouts = [original + extra, original + duplicate_data,
                   original[:36] + duplicate_fmt + original[36:],
                   original[:12] + original[36:] + original[12:36]]
        for raw in layouts:
            malformed = bytearray(raw)
            malformed[4:8] = (len(malformed) - 8).to_bytes(4, "little")
            self.calls.clear()
            with self.subTest(layout=len(malformed)), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(original_wav=bytes(malformed),
                          source_sha256=sha256(malformed).hexdigest())
            self.assertEqual(self.calls, [])

    def test_large_riff_metadata_denied_without_private_audio_egress(self):
        # Self-consistent RIFF metadata must not consume the entire WAV budget.
        # Keep the real original PCM payload and hash valid in both cases.
        def with_junk(size):
            chunk = b"JUNK" + size.to_bytes(4, "little") + b"x" * size
            raw = bytearray(self.original[:36] + chunk + self.original[36:])
            raw[4:8] = (len(raw) - 8).to_bytes(4, "little")
            return bytes(raw)

        # Below the bound is permitted and retains original word timings.
        accepted = with_junk(1024)
        self.assertEqual(self.call(original_wav=accepted,
                         source_sha256=sha256(accepted).hexdigest())["language"], "hi")
        self.assertEqual(len(self.calls), 1)
        self.calls.clear()
        # A 1 MiB JUNK chunk plus fmt metadata exceeds the cumulative bound.
        oversized = with_junk(1024 * 1024)
        with self.assertRaises(VoiceStudioTranscriptionDenied):
            self.call(original_wav=oversized,
                      source_sha256=sha256(oversized).hexdigest())
        self.assertEqual(self.calls, [])

    def test_pcm_format_parity_denies_inconsistent_headers_before_egress(self):
        # The signed-media verifier requires strict 16-bit PCM, valid byte rate,
        # block alignment, 8-48 kHz sample rate and canonical fmt length.
        # Each case has a self-consistent RIFF length and SHA256.
        variants = []
        for offset, value, width in (
            (20, 3, 2),       # non-PCM codec
            (22, 3, 2),       # three channels
            (24, 96000, 4),  # outside signed-media sample-rate ceiling
            (28, 1, 4),      # inconsistent byte rate
            (32, 8, 2),      # inconsistent block alignment
            (34, 24, 2),     # unsupported bits per sample
        ):
            changed = bytearray(self.original)
            changed[offset:offset + width] = value.to_bytes(width, "little")
            variants.append(bytes(changed))
        # A fmt chunk with extra opaque bytes must also fail even when the
        # downstream WAV decoder might ignore the extension.
        extended = bytearray(self.original[:36] + b"XX" + self.original[36:])
        extended[16:20] = (18).to_bytes(4, "little")
        extended[4:8] = (len(extended) - 8).to_bytes(4, "little")
        variants.append(bytes(extended))
        for malformed in variants:
            with self.subTest(header=malformed[20:36]):
                self.calls.clear()
                with self.assertRaises(VoiceStudioTranscriptionDenied):
                    self.call(original_wav=malformed,
                              source_sha256=sha256(malformed).hexdigest())
                self.assertEqual(self.calls, [])
        self.assertEqual(self.call()["language"], "hi")

    def test_partial_pcm_frame_denied_before_private_asr_egress(self):
        # Python's wave reader floors a partial PCM frame; the signed source
        # must not include a dangling byte that the ASR decoder may interpret
        # differently. Exercise both mono and stereo block alignment.
        for channels in (1, 2):
            output = io.BytesIO()
            with wave.open(output, "wb") as writer:
                writer.setnchannels(channels)
                writer.setsampwidth(2)
                writer.setframerate(16000)
                writer.writeframes(bytes([0]) * (channels * 2 * 32000))
            canonical = output.getvalue()
            self.calls.clear()
            self.assertEqual(self.call(original_wav=canonical,
                source_sha256=sha256(canonical).hexdigest())["language"], "hi")
            self.assertEqual(len(self.calls), 1)
            for remainder in range(1, channels * 2):
                # Preserve valid RIFF size and original-byte SHA; only the
                # declared data length is inconsistent with PCM sample frames.
                malformed = bytearray(canonical + bytes([0]) * remainder)
                malformed[4:8] = (len(malformed) - 8).to_bytes(4, "little")
                malformed[40:44] = (len(malformed) - 44).to_bytes(4, "little")
                if remainder % 2:
                    malformed.append(0)  # canonical odd RIFF padding
                    malformed[4:8] = (len(malformed) - 8).to_bytes(4, "little")
                self.calls.clear()
                with self.subTest(channels=channels, remainder=remainder):
                    with self.assertRaises(VoiceStudioTranscriptionDenied):
                        self.call(original_wav=bytes(malformed),
                            source_sha256=sha256(malformed).hexdigest())
                    self.assertEqual(self.calls, [])

    def test_zero_sample_rate_wav_fails_closed_without_egress(self):
        # RIFF header may be structurally readable while PCM rate is zero.
        # The worker must raise its domain denial, never ZeroDivisionError.
        malformed = bytearray(self.original)
        malformed[24:28] = (0).to_bytes(4, "little")
        malformed[28:32] = (0).to_bytes(4, "little")
        self.calls.clear()
        with self.assertRaises(VoiceStudioTranscriptionDenied):
            self.call(original_wav=bytes(malformed),
                      source_sha256=sha256(malformed).hexdigest())
        self.assertEqual(self.calls, [])

    def test_malformed_locale_inputs_never_egress(self):
        for language in ([], {}, 7, True, ["hi"], {"locale": "hi"}):
            self.calls.clear()
            with self.subTest(language=repr(language)), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(language=language)
            self.assertEqual(self.calls, [])

    def test_malformed_upstream_language_never_reaches_signed_review(self):
        for reported in ("", "hi\x00", "hi\n", "\ud800", "fr", "en-US", "HI", [], {}, 42, True):
            self.payload["language"] = reported
            def sender(req, timeout):
                return Reply(json.dumps(self.payload, ensure_ascii=True).encode("ascii"))
            with self.subTest(reported=repr(reported)), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(language=None, transport=sender)
        self.payload["language"] = "mr"
        self.assertEqual(self.call(language="mr")["language"], "mr")

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
        ]
        for words in invalid:
            self.payload["words"] = words
            with self.subTest(words=words), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call()
        self.payload["words"] = [{"start":0.1,"end":0.7,"word":"\ud800"}]
        # Use escaped JSON so the invalid surrogate reaches the parser rather
        # than failing UTF-8 encoding in the test transport itself.
        def escaped_sender(req, timeout):
            return Reply(json.dumps(self.payload).encode("ascii"))
        with self.assertRaises(VoiceStudioTranscriptionDenied):
            self.call(transport=escaped_sender)
        self.payload["words"] = [
            {"start":0.1001,"end":0.7001,"word":"नमस्ते"},
            {"start":0.8001,"end":1.5001,"word":"दुनिया"},
        ]
        result = self.call()
        self.assertEqual(result["words"][0],
                         {"start":0.1,"end":0.7,"word":"नमस्ते"})

    def test_unsafe_transcript_text_denied_before_signed_handoff(self):
        # Words can be valid while the top-level transcript carries controls
        # or an unpaired surrogate. Neither may enter review/caption artifacts.
        for value in ("hello\x00world", "hello\nworld", "\ud800",
                      "valid " + "\udfff", "x" * 12001):
            self.payload["text"] = value
            def escaped_sender(req, timeout):
                return Reply(json.dumps(self.payload, ensure_ascii=True).encode("ascii"))
            with self.subTest(text=repr(value)), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(transport=escaped_sender)
        self.payload["text"] = "नमस्ते दुनिया"
        self.assertEqual(self.call()["text"], "नमस्ते दुनिया")

    def test_bidi_control_spoofing_denied_before_review(self):
        for control in ("\u202e", "\u202a", "\u2066", "\u2069", "\u200f", "\u061c"):
            self.payload["words"] = [{"start": 0.1, "end": 0.7, "word": "नम" + control + "स्ते"}]
            with self.subTest(field="word", control=hex(ord(control))), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call()
            self.payload["words"] = [{"start": 0.1, "end": 0.7, "word": "नमस्ते"}]
            self.payload["text"] = "नम" + control + "स्ते"
            with self.subTest(field="text", control=hex(ord(control))), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call()
        self.payload["text"] = "नमस्ते दुनिया"
        self.assertEqual(self.call()["words"][0]["word"], "नमस्ते")

    def test_invisible_unicode_and_c1_controls_denied_in_word_and_text(self):
        # C1/DEL controls, line separators and BOM can hide or visually split
        # Indic captions even though they are not ASCII control characters.
        # Legitimate Devanagari combining marks remain permitted.
        for control in (chr(0x7f), chr(0x85), chr(0x9f), chr(0x2028), chr(0x2029), chr(0xfeff)):
            for field in ("word", "text"):
                self.payload["words"] = [{"start": 0.1, "end": 0.7, "word": "नमस्ते"}]
                self.payload["text"] = "नमस्ते"
                if field == "word":
                    self.payload["words"][0]["word"] += control
                else:
                    self.payload["text"] += control
                with self.subTest(field=field, codepoint=hex(ord(control))):
                    with self.assertRaises(VoiceStudioTranscriptionDenied):
                        self.call()
        self.payload["words"] = [{"start": 0.1, "end": 0.7, "word": "नमस्ते"}]
        self.payload["text"] = "नमस्ते"
        self.assertEqual(self.call()["words"][0]["word"], "नमस्ते")

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

    def test_duplicate_json_keys_at_every_depth_are_denied(self):
        # Never accept parser-dependent first/last-key interpretations before
        # a review can be converted into a signed tenant-scoped transcript.
        base = json.dumps(self.payload, ensure_ascii=False)
        variants = [
            base.replace('"task": "transcribe"',
                         '"task": "translate", "task": "transcribe"', 1),
            base.replace('"language": "hi"',
                         '"language": "mr", "language": "hi"', 1),
            base.replace('"start": 0.1',
                         '"start": 1.9, "start": 0.1', 1),
            base.replace('"word": "नमस्ते"',
                         '"word": "spoof", "word": "नमस्ते"', 1),
        ]
        for body in variants:
            self.assertNotEqual(body, base)
            with self.subTest(body=body[:100]), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(transport=lambda req, timeout, body=body:
                          Reply(body.encode("utf-8")))
        # Valid Indic JSON remains accepted, including nested word objects.
        self.assertEqual(self.call()["words"][0]["word"], "नमस्ते")

    def test_nonstandard_json_constants_denied_even_in_ignored_metadata(self):
        # Python's JSON decoder otherwise accepts NaN/Infinity as extensions.
        # A signed review must originate from standards-compliant JSON only.
        base = json.dumps(self.payload, ensure_ascii=False)
        for constant in ("NaN", "Infinity", "-Infinity"):
            body = base[:-1] + ', "untrusted_metadata": ' + constant + '}'
            with self.subTest(constant=constant), self.assertRaises(VoiceStudioTranscriptionDenied):
                self.call(transport=lambda req, timeout, body=body:
                          Reply(body.encode("utf-8")))
        self.assertEqual(self.call()["language"], "hi")

    def test_excessive_json_nesting_fails_closed_with_domain_denial(self):
        # A small, deeply nested unknown field can exceed Python's JSON
        # recursion limit even when the HTTP response is below MAX_JSON.
        # Never leak RecursionError or pass an ambiguous review downstream.
        base = json.dumps(self.payload, ensure_ascii=False)
        deeply_nested = "[" * 1500 + "0" + "]" * 1500
        body = base[:-1] + ', "ignored": ' + deeply_nested + "}"
        with self.assertRaises(VoiceStudioTranscriptionDenied):
            self.call(transport=lambda req, timeout: Reply(body.encode("utf-8")))
        # A normal Indic response still reaches the review-only adapter.
        self.assertEqual(self.call()["words"][0]["word"], "नमस्ते")

    def test_upstream_error_redacted(self):
        from urllib.error import URLError
        def sender(req,timeout):
            raise URLError("secret should not be returned")
        with self.assertRaises(VoiceStudioTranscriptionDenied) as e:
            self.call(transport=sender)
        self.assertNotIn("secret",str(e.exception))


if __name__=="__main__":
    unittest.main()
