"""Bounded CPU subprocess regression; no model, media, network or GPU required."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
JS = r"""
import {runBoundedOfflineCommand, OfflineAsrError}
  from './video-engine/feature7/offline_whisperx_cpu.mjs';
const mode = process.argv[1];
const outcomes = {
  success: ['-e', 'process.exit(0)'],
  failure: ['-e', 'process.exit(7)'],
  timeout: ['-e', 'process.on("SIGTERM",()=>{});setInterval(()=>{},1000)']
};
const timeout = mode === 'timeout' ? 300 : mode === 'invalid' ? 0 : 1500;
try {
  runBoundedOfflineCommand(process.execPath,
    outcomes[mode] || outcomes.success, timeout, process.env, 'Offline CPU worker');
  process.stdout.write(JSON.stringify({ok:true}));
} catch (e) {
  process.stdout.write(JSON.stringify({
    ok:false, typed:e instanceof OfflineAsrError,
    safeMessage:e.message.includes('no transcript approved') ||
      e.message.includes('Invalid bounded offline command')
  }));
}
"""

@unittest.skipUnless(shutil.which("node"), "Node required for Feature7 CPU worker")
class Feature7OfflineWorkerTimeoutTests(unittest.TestCase):
    def invoke(self, mode):
        result = subprocess.run(
            ["node", "--input-type=module", "-e", JS, mode],
            cwd=ROOT, capture_output=True, text=True, timeout=8
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_successful_offline_process(self):
        self.assertEqual(self.invoke("success"), {"ok": True})

    def test_nonzero_exit_fails_closed(self):
        self.assertEqual(
            self.invoke("failure"),
            {"ok": False, "typed": True, "safeMessage": True}
        )

    def test_ignores_sigterm_but_cannot_escape_hard_timeout(self):
        # A child deliberately left running must not outlive the CPU deadline.
        self.assertEqual(
            self.invoke("timeout"),
            {"ok": False, "typed": True, "safeMessage": True}
        )

    def test_zero_timeout_rejected(self):
        self.assertEqual(
            self.invoke("invalid"),
            {"ok": False, "typed": True, "safeMessage": True}
        )

if __name__ == "__main__":
    unittest.main()
