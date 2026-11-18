"""Feature7 AutoBroll-derived speech gap review-only source-coordinate checks."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {suggestGapCuts} from './video-engine/feature7/gap_cut_advisory.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(suggestGapCuts(p)));
"""


def input_fixture():
    return {
      'asset_id':'private-upload-a','source_scene_index':0,
      'source_duration_seconds':16,'target_duration_seconds':15,
      'words':[
        {'word':'Welcome','startMs':500,'endMs':800},
        {'word':'everyone.','startMs':870,'endMs':1200},
        {'word':'New','startMs':3700,'endMs':3950},
        {'word':'stock.','startMs':4020,'endMs':4300},
        {'word':'Visit','startMs':12300,'endMs':12600},
        {'word':'today.','startMs':12680,'endMs':13100},
      ],'max_removals':8
    }


@unittest.skipUnless(shutil.which('node'),'Node required')
class Feature7GapCutPreviewTests(unittest.TestCase):
    def run_js(self,data):
        return subprocess.run(['node','--input-type=module','-e',JS],
          input=json.dumps(data),cwd=ROOT,text=True,capture_output=True,timeout=10)

    def test_gap_cuts_are_audio_preserving_advisories(self):
        r=self.run_js(input_fixture())
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertFalse(out['approved'])
        self.assertFalse(out['feature4_executable'])
        self.assertTrue(out['advisory_only'])
        self.assertTrue(out['no_auto_deletion'])
        self.assertGreaterEqual(len(out['removable_gap_candidates']),2)
        self.assertTrue(all(x['proposed_remove_ms']>=250 for x in
                            out['removable_gap_candidates']))
        self.assertTrue(all(x['preserve_original_audio'] for x in
                            out['removable_gap_candidates']))
        self.assertEqual(out['source_duration_ms'],16000)
        self.assertLess(out['remaining_if_all_candidates_removed_ms'],16000)

    def test_short_isolated_utterance_is_never_proposed_for_deletion(self):
        # speechRuns filters very short runs. A meaningful short word such as
        # "no" must still fence the source interval against deletion.
        p=input_fixture()
        p['words'].insert(4, {'word':'no','startMs':7200,'endMs':7240})
        r=self.run_js(p)
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertGreaterEqual(len(out['removable_gap_candidates']),1)
        for gap in out['removable_gap_candidates']:
            for word in p['words']:
                self.assertFalse(
                    word['startMs'] < gap['source_end_ms'] and
                    word['endMs'] > gap['source_start_ms'],
                    f"Candidate would erase speech: {gap}, {word}")
        self.assertEqual(
            out['potential_removed_ms'],
            sum(g['proposed_remove_ms'] for g in out['removable_gap_candidates']))
        self.assertTrue(out['advisory_only'])
        self.assertFalse(out['feature4_executable'])

    def test_empty_words_do_not_invent_speech_gaps(self):
        p=input_fixture()
        p['words']=[]
        r=self.run_js(p)
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        self.assertEqual(result['detected_speech_ranges'],[])
        self.assertEqual(result['removable_gap_candidates'],[])

    def test_boundaries_and_overlaps_fail_closed(self):
        for mutation in ('out_of_source','negative','reversed','empty_word',
                         'bad_target','huge_duration','unsupported_scene'):
            with self.subTest(mutation=mutation):
                p=input_fixture()
                if mutation=='out_of_source':p['words'][-1]['endMs']=20000
                if mutation=='negative':p['words'][0]['startMs']=-1
                if mutation=='reversed':p['words'][1]['startMs']=100
                if mutation=='empty_word':p['words'][0]['word']=''
                if mutation=='bad_target':p['target_duration_seconds']=18
                if mutation=='huge_duration':p['source_duration_seconds']=8000
                if mutation=='unsupported_scene':p['source_scene_index']=-2
                r=self.run_js(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_limit_is_honored_without_retiming_source(self):
        p=input_fixture()
        p['max_removals']=1
        result=self.run_js(p)
        self.assertEqual(result.returncode,0,result.stderr)
        parsed=json.loads(result.stdout)
        self.assertEqual(len(parsed['removable_gap_candidates']),1)
        self.assertTrue(all(s['source_start_ms']>=0 for s in
                            parsed['detected_speech_ranges']))


if __name__=='__main__':
    unittest.main()
