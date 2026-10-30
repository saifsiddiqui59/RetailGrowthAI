"""Speech-reference WER and cue timing: honest model-independent CPU benchmark."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {evaluateSpeechAgainstReference}
  from './video-engine/feature7/speech_quality.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(evaluateSpeechAgainstReference(p)));
"""
SHA='a'*64
REFERENCE="""1
00:00:00,500 --> 00:00:01,300
Welcome to our store.

2
00:00:02,000 --> 00:00:02,900
Shop with us today.
"""

def fixture():
    return {
      'reference_srt':REFERENCE,
      'source_duration_seconds':5,
      'expected_source_sha256':SHA,
      'normalized_asr':{
        'source_sha256':SHA,
        'words':[
          {'word':'Welcome','startMs':520,'endMs':630},
          {'word':'to','startMs':640,'endMs':750},
          {'word':'our','startMs':770,'endMs':930},
          {'word':'store.','startMs':950,'endMs':1190},
          {'word':'Shop','startMs':2030,'endMs':2200},
          {'word':'with','startMs':2220,'endMs':2370},
          {'word':'us','startMs':2420,'endMs':2540},
          {'word':'today.','startMs':2590,'endMs':2820},
        ]
      }
    }

@unittest.skipUnless(shutil.which('node'),'Requires Node')
class SpeechReferenceBenchmarkTests(unittest.TestCase):
    def evaluate(self,p):
        return subprocess.run(['node','--input-type=module','-e',JS],
          cwd=ROOT,input=json.dumps(p),capture_output=True,text=True,timeout=10)

    def test_exact_words_and_cue_timing_pass_but_are_not_model_proof(self):
        r=self.evaluate(fixture())
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads(r.stdout)
        self.assertEqual(data['word_error_rate'],0)
        self.assertEqual(data['cue_coverage_ratio'],1)
        self.assertTrue(data['thresholds_passed'])
        self.assertTrue(data['benchmark_only'])
        self.assertFalse(data['actual_model_inference_proven'])
        self.assertFalse(data['model_weights_license_verified'])
        self.assertFalse(data['customer_release_ready'])

    def test_hallucinated_words_fail_word_accuracy(self):
        p=fixture()
        for word in p['normalized_asr']['words']:word['word']='wrong'
        r=self.evaluate(p)
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertGreater(out['word_error_rate'],.8)
        self.assertFalse(out['thresholds_passed'])

    def test_transcript_outside_reference_timing_fails_coverage(self):
        p=fixture()
        for i,w in enumerate(p['normalized_asr']['words']):
            w['startMs']=4200+i*75
            w['endMs']=4250+i*75
        r=self.evaluate(p)
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads(r.stdout)
        self.assertEqual(data['word_error_rate'],0)
        self.assertEqual(data['cue_coverage_ratio'],0)
        self.assertFalse(data['thresholds_passed'])

    def test_global_word_match_does_not_hide_wrong_cue_timing(self):
        p=fixture()
        # Every recognized token is correct and ordered, but only one word
        # per subtitle occurs inside its actual spoken cue. Global WER=0
        # must not be mistaken for acceptable local caption alignment.
        intervals=[(520,630),(1450,1490),(1500,1540),(1550,1590),
                   (2050,2120),(3200,3240),(3300,3340),(3400,3440)]
        for w,(start,end) in zip(p['normalized_asr']['words'],intervals):
            w['startMs'],w['endMs']=start,end
        r=self.evaluate(p)
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads(r.stdout)
        self.assertEqual(data['word_error_rate'],0)
        self.assertLess(data['cue_coverage_ratio'],.8)
        self.assertTrue(data['cue_word_alignment_required'])
        self.assertFalse(data['thresholds_passed'])
        self.assertFalse(data['customer_release_ready'])

    def test_punctuation_only_asr_word_is_not_speech_evidence(self):
        p=fixture()
        p['normalized_asr']['words'][0]['word']='...'
        r=self.evaluate(p)
        self.assertNotEqual(r.returncode,0,r.stdout)

    def test_foreign_source_bad_srt_and_out_of_range_words_fail(self):
        bad_cases=[]
        p=fixture();p['normalized_asr']['source_sha256']='b'*64;bad_cases.append(p)
        p=fixture();p['reference_srt']='Hello world';bad_cases.append(p)
        p=fixture();p['reference_srt']=REFERENCE.replace('00:00:02,900','00:00:06,900');bad_cases.append(p)
        p=fixture();p['normalized_asr']['words'][1]['startMs']=-200;bad_cases.append(p)
        p=fixture();p['normalized_asr']['words'][0]['endMs']=999999;bad_cases.append(p)
        for n,p in enumerate(bad_cases):
            with self.subTest(index=n):
                r=self.evaluate(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

if __name__=='__main__':
    unittest.main()
