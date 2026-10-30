"""Original measured waveform beat-grid and strict editor cut snapping."""
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from beat_grid import beat_grid
from feature4_beat_edit import original_rhythmic_music, snap_scene_cuts, BeatEditError

class Feature4BeatEditTests(unittest.TestCase):
    def setUp(self):
        self.ctx=tempfile.TemporaryDirectory()
        self.addCleanup(self.ctx.cleanup)
        self.wav=Path(self.ctx.name)/"original.wav"

    def test_detect_actual_percussion_and_retime_to_measured_onsets(self):
        beats=original_rhythmic_music(self.wav,seconds=15)
        self.assertEqual(beats,beat_grid(self.wav,duration_seconds=15))
        self.assertGreater(len(beats),10)
        self.assertTrue(all(any(abs(b-t)<.08 for b in beats) for t in (5,10,12)))
        original=[(0,5,"look01","First"),(5,5,"garment01","Details"),
                  (10,2,"look02","Motion"),(12,3,None,"Closing")]
        snapped=snap_scene_cuts(original,beats,duration_seconds=15)
        self.assertEqual([item[2] for item in snapped],[x[2] for x in original])
        self.assertTrue(all(abs(snapped[i][0]-original[i][0])<.08
                            for i in range(1,len(original))))
        self.assertTrue(all(min(abs(x[0]-b) for b in beats)<=.17
                            for x in snapped[1:]))
        self.assertAlmostEqual(sum(x[1] for x in snapped),15,places=3)
        with wave.open(str(self.wav)) as reader:
            self.assertEqual(reader.getnframes(),15*22050)

    def test_missing_beat_fails_closed_without_fabricated_timing(self):
        original=[(0,5,"a","X"),(5,5,"b","Y"),(10,5,None,"Z")]
        with self.assertRaisesRegex(BeatEditError,"No detected"):
            snap_scene_cuts(original,[1.0,2.0,3.0],duration_seconds=15)

    def test_invalid_grid_and_unapproved_scene_timing_rejected(self):
        scene=[(0,5,"a","X"),(5,10,None,"Z")]
        for grid in ([5.1,5.1],[float("nan"),5.0],[15.0,5.0],
                     [6.0,4.0],[]):
            with self.assertRaises(BeatEditError):
                snap_scene_cuts(scene,grid,duration_seconds=15)
        with self.assertRaises(BeatEditError):
            snap_scene_cuts([(0,5,"a","X"),(6,9,None,"Z")],
                            [5.0,6.0],duration_seconds=15)
        with self.assertRaises(BeatEditError):
            original_rhythmic_music(self.wav,seconds=12)

    def test_music_output_never_overwrites_existing(self):
        original_rhythmic_music(self.wav,seconds=15)
        before=self.wav.read_bytes()
        with self.assertRaisesRegex(BeatEditError,"new/private"):
            original_rhythmic_music(self.wav,seconds=15)
        self.assertEqual(before,self.wav.read_bytes())

if __name__=="__main__":
    unittest.main()
