"""Feature7 independent CPU WAV parser/transcript adversarial regressions.

Real PCM16 WAVs and actual Node code, not an ASR model nor approval fixture.
Tests cover noncanonical source that Python wave might accept but an immutable
F7 private original WAV MUST reject before processing/sending to Feature2.
"""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave

ROOT=Path(__file__).resolve().parents[2]
SOURCE_JS=r"""
import fs from 'node:fs';
import {inspectOriginalPrivatePCM16Wav} from './video-engine/feature7/original_wav_cpu.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const v=inspectOriginalPrivatePCM16Wav(p);
process.stdout.write(JSON.stringify({duration:v.duration_seconds,sha:v.source_sha256}));
"""
TRANSCRIPT_JS=r"""
import fs from 'node:fs';
import {normalizeWhisperx} from './video-engine/feature7/transcript_adapter.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const v=normalizeWhisperx(p);
process.stdout.write(JSON.stringify({words:v.words,digest:v.transcript_sha256}));
"""

@unittest.skipUnless(shutil.which("node"),"Node.js required")
class Feature7CpuFormatAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="f7-asr-hardening-")
        self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.video=self.home/"source.wav"
        with wave.open(str(self.video),"wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\0\0"*16000)
        self.initial=self.video.read_bytes()
        self.sha=hashlib.sha256(self.initial).hexdigest()

    def go(self,script,payload):
        return subprocess.run(["node","--input-type=module","-e",script],
            cwd=ROOT,input=json.dumps(payload,ensure_ascii=True),
            capture_output=True,text=True,timeout=12)

    def inspect(self,data):
        self.video.write_bytes(data)
        return self.go(SOURCE_JS,{"root":str(self.home),
          "relative_path":"source.wav",
          "expected_sha256":hashlib.sha256(data).hexdigest()})

    @staticmethod
    def riff(chunks):
        body=b"WAVE"+b"".join(
            tag+struct.pack("<I",len(data))+data+(b"\0" if len(data)%2 else b"")
            for tag,data in chunks)
        return b"RIFF"+struct.pack("<I",len(body))+body

    def test_exact_original_pcm_succeeds(self):
        p=self.inspect(self.initial)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)["duration"],1)

    def test_malformed_chunks_are_denied_before_inference(self):
        fmt=self.initial[20:36]
        pcm=self.initial[44:]
        variants={
          "trailing_payload":self.initial+b"xy",
          "duplicate_fmt":self.riff([(b"fmt ",fmt),(b"fmt ",fmt),(b"data",pcm)]),
          "data_before_fmt":self.riff([(b"data",pcm),(b"fmt ",fmt)]),
          "post_audio_chunk":self.riff([(b"fmt ",fmt),(b"data",pcm),(b"JUNK",b"hi")]),
          "unsupported_format":self.riff([(b"fmt ",b"\x03\x00"+fmt[2:]),
                                            (b"data",pcm)]),
          "fmt_size_18":self.riff([(b"fmt ",fmt+b"\x00\x00"),(b"data",pcm)]),
          "unknown_chunk":self.riff([(b"fmt ",fmt),(b"ABCD",b"foo"),(b"data",pcm)]),
          "partial_riff_chunk":self.initial[:-2],
          "oversized_junk":self.riff([(b"fmt ",fmt),
                                     (b"JUNK",b"0"*65538),(b"data",pcm)]),
          "zero_pcm":self.riff([(b"fmt ",fmt),(b"data",b"")])
        }
        for name,data in variants.items():
            with self.subTest(name=name):
                p=self.inspect(data)
                self.assertNotEqual(p.returncode,0,p.stdout)

    def transcript(self,words):
        return self.go(TRANSCRIPT_JS,{
          "shop_id":"shop","asset_id":"asset",
          "source_sha256":"a"*64,"source_duration_seconds":5,
          "transcript":{"segments":[{"words":words}]}
        })

    def test_devanagari_combining_marks_and_repeated_words_preserved(self):
        p=self.transcript([{"word":"दीवाली","start":.2,"end":.5},
                           {"word":"दीवाली","start":.6,"end":.8},
                           {"word":"साड़ी","start":1,"end":1.4}])
        self.assertEqual(p.returncode,0,p.stderr)
        out=json.loads(p.stdout)
        self.assertEqual([w["word"] for w in out["words"]],
                         ["दीवाली","दीवाली","साड़ी"])
        self.assertEqual(out["words"][-1]["endMs"],1400)

    def test_bidi_controls_surrogate_missing_timestamp_and_reorder_denied(self):
        good={"word":"Welcome","start":.2,"end":.4}
        bad=[
          {"word":"\u202ehidden","start":.2,"end":.4},
          {"word":"\x00hidden","start":.2,"end":.4},
          {"word":"\ud800","start":.2,"end":.4},
          {"word":"x","start":.2},
          {"word":"x","start":2,"end":1},
          {"word":"x","start":10,"end":11},
        ]
        for word in bad:
            with self.subTest(word=repr(word)):
                self.assertNotEqual(self.transcript([word]).returncode,0)
        self.assertNotEqual(self.transcript([
          good,{"word":"later","start":.01,"end":.1}
        ]).returncode,0)


if __name__=="__main__":
    unittest.main()
