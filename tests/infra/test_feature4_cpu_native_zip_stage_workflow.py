"""Guard a sealed native CPU worker package stage from auto-activation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
W=ROOT/".github/workflows/retail-dev-feature4-cpu-zip-once.yml"


class F4CpuZipStageWorkflowContract(unittest.TestCase):
    def test_isolated_main_only_protected_dev(self):
        src=W.read_text()
        for token in ("branches: [main]",
            "'.github/workflows/retail-dev-feature4-cpu-zip-once.yml'",
            "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
            "github.ref == 'refs/heads/main'",
            "environment: dev",
            "id-token: write",
            "persist-credentials: false",
            "az account show --query id",
            "rgai-dev-f4cpu-d4e5ddbd",
            "rg-retailgrowth-dev",
            "rgaid4e5ddbdf0d21d96"):
            self.assertIn(token,src)
        self.assertNotIn("schedule:",src)
        self.assertNotIn("pull_request:",src)

    def test_off_flags_and_both_private_queues_before_publish(self):
        src=W.read_text()
        for token in (
            "retail-feature4-cpu-render retail-feature4-cpu-render-poison",
            "RETAIL_FEATURE4_CPU_WORKER_ENABLED",
            "RETAIL_FEATURE4_CPU_RENDER_ENABLED",
            "scale.get('maximumInstanceCount') != 1",
            "scale.get('instanceMemoryMB') != 2048",
            "runtime.get('name')!='python' or runtime.get('version')!='3.11'",
            "Azure/functions-action@c5060b3b8bb1ebbcb531abd00c822ecbaa8ea656",
        ):
            self.assertIn(token,src)
        self.assertNotIn("az functionapp config appsettings set",src)
        self.assertNotIn("az role assignment create",src)
        self.assertNotIn("--auth-mode key",src)

    def test_sources_sealed_before_azure_publish(self):
        src=W.read_text()
        for token in (
            "ffmpeg-n8.1.3-36-ge22a4510c9-linux64-gpl-8.1.tar.xz",
            "fce424851b0a982bdd4ac4e96f0e7b32cf29de999e54500676d41ad175ed0c79",
            "npm ci --prefix video-engine/hyperframes",
            "lock_guard.py",
            "browsers install chrome-headless-shell",
            "uv python install 3.11",
            "package_feature4_cpu.py --build",
            "verify_feature4_cpu_release.py",
            "sha256sum --check",
            "RETAIL_FEATURE4_CPU_RENDER_ENABLED",
        ):
            self.assertIn(token,src)
        self.assertLess(src.index("verify_feature4_cpu_release.py"), src.index("uses: Azure/functions-action@"))
        self.assertNotIn("actions/upload-artifact",src)
        self.assertNotIn("FEATURE4_CPU_WORKER_ENABLED: 'true'",src)


if __name__=="__main__":
    unittest.main()
