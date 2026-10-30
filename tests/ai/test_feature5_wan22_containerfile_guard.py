"""Source-only GPU-OFF container build checklist; never runs Docker or CUDA."""
import re
import unittest
from pathlib import Path


class WanContainerfileGuardTests(unittest.TestCase):
    def test_offline_review_required_containerfile_never_implicitly_builds(self):
        root=Path(__file__).resolve().parents[2]
        path=root/"feature5_motion"/"infra"/"Containerfile.wan22.REVIEW_REQUIRED"
        s=path.read_text()
        commands=[
            line.strip() for line in s.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertIn("ARG REVIEWED_CUDA_PYTHON_BASE",commands)
        self.assertIn("FROM $REVIEWED_CUDA_PYTHON_BASE",commands)
        self.assertNotRegex(s,r"(?im)^\s*FROM\s+\S+:(?:latest|main|stable)\b")
        self.assertIn("ARG EXPECTED_COMFYUI_COMMIT=79cf64c21a1dba50749945ba9fe2e3a692f45438",s)
        self.assertIn("test -f /opt/retailgrowth/comfyui/LICENSE",s)
        self.assertIn("COPY vendor/reviewed-source-files.sha256.json",s)
        self.assertIn("COPY feature5_motion/infra/wan22_source_audit.py",s)
        self.assertIn("python /opt/retailgrowth/source_audit.py --source /opt/retailgrowth/comfyui",s)
        self.assertIn("--manifest /opt/retailgrowth/source-review.json",s)
        self.assertLess(s.index("python /opt/retailgrowth/source_audit.py"),s.index("python -m pip install"))
        self.assertIn("PIP_NO_INDEX=1",s)
        self.assertIn("PIP_REQUIRE_HASHES=1",s)
        self.assertIn("--no-index --require-hashes",s)
        self.assertIn("python -m pip check",s)
        self.assertIn("USER 10001:10001",s)
        self.assertIn('["sh","-c","umask 077; exec python main.py --listen 127.0.0.1',s)
        self.assertIn("install -d -m 0700 -o 10001 -g 10001",s)
        for arg in ("--input-directory","--output-directory",
                    "--temp-directory","--user-directory","--disable-metadata"):
            self.assertIn(arg,s)
        self.assertIn("/opt/retailgrowth/private-runtime/input",s)
        self.assertIn("/opt/retailgrowth/private-runtime/output",s)
        self.assertLess(s.index("install -d -m 0700"),s.index("USER 10001:10001"))
        for forbidden in (
            r"(?im)^\s*EXPOSE\s+",r"(?im)^\s*RUN.*\bcurl\b",
            r"(?im)^\s*RUN.*\bwget\b",r"(?im)^\s*RUN.*\bgit clone\b",
            r"(?im)^\s*RUN.*pip install.*https?://",
        ):
            with self.subTest(pattern=forbidden):
                self.assertIsNone(re.search(forbidden,s))
        # The source file is explicitly a plan, not a built verified image.
        self.assertIn("Missing inputs intentionally make this unbuildable",s)


if __name__=="__main__":
    unittest.main()
