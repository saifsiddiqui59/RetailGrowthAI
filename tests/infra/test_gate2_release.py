"""Workstream Q offline Gate 2 release tests. Synthetic ELF is NOT deployable."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    location = ROOT / "scripts/deploy" / (name + ".py")
    spec = importlib.util.spec_from_file_location("q_test_" + name, location)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = load("release_package")
package = load("package")

BASE_PARAMS = {
    "environmentName": "dev",
    "location": "centralindia",
    "storageAccountName": "rgaidevtest007",
    "functionAppName": "rgai-dev-functions",
    "functionPlanName": "rgai-dev-flex",
    "frontendOrigin": "https://rgai-dev-123.azurestaticapps.net",
}


def write_params(directory, values=None):
    file = directory / "params.json"
    file.write_text(json.dumps({"parameters": {
        k: {"value": v} for k, v in (values or BASE_PARAMS).items()
    }}))
    return file


def elf():
    binary = bytearray(100_000)
    binary[:7] = b"\x7fELF\x02\x01\x01"
    struct.pack_into("<H", binary, 18, 62)
    struct.pack_into("<Q", binary, 32, 64)
    struct.pack_into("<HH", binary, 54, 56, 1)
    struct.pack_into("<I", binary, 64, 1)
    return bytes(binary)


def write_test_zip(path, *, damage_trigger=False, suffix=b""):
    data = package.source_files()
    if damage_trigger:
        name = "azure-functions/campaign-api/function_app.py"
        data[name] = data[name].replace(b"retail-reel-render-poison",
                                        b"unrecognized-poison")
    data["ai_agents/__init__.py"] += suffix
    data.update({
        "bin/ffmpeg": elf(),
        "bin/ffprobe": elf(),
        "bin/THIRD_PARTY_NOTICES.txt": b"TEST FIXTURE ONLY -- NOT LICENSED",
    })
    package.write_zip(path, data)
    return path


class Gate2ReleaseTests(unittest.TestCase):
    def test_parameter_validator_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertEqual(gate.parameters(write_params(folder)), BASE_PARAMS)
            for key, value in (
                ("environmentName", "prod"),
                ("location", "eastus"),
                ("frontendOrigin", "https://*.example.test"),
                ("frontendOrigin", "http://rgai-dev-123.azurestaticapps.net"),
                ("frontendOrigin", "https://rgai-dev-123.azurestaticapps.net/path"),
                ("storageAccountName", "ReplaceMe"),
                ("functionAppName", "wineshop-dev-functions"),
                ("maxInstances", 7),
                ("maxInstances", True),
                ("instanceMemoryMB", 4096),
            ):
                invalid = dict(BASE_PARAMS)
                invalid[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    gate.parameters(write_params(folder, invalid))
            invalid = dict(BASE_PARAMS, ServiceSecret="sensitive")
            with self.assertRaises(ValueError):
                gate.parameters(write_params(folder, invalid))

    def test_manifest_is_unapproved_and_covers_all_triggers(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            params = write_params(folder)
            candidate = write_test_zip(folder / "candidate.zip")
            manifest = gate.prepare(params, candidate, "a" * 40, 200.0, first=True)
            self.assertEqual(manifest["approval_status"], "NOT_APPROVED")
            self.assertIsNone(manifest["last_good_sha256"])
            self.assertEqual(manifest["queue_triggers"], gate.QUEUES)
            self.assertEqual(manifest["host_timeout_seconds"], 1200)
            self.assertEqual(manifest["claim_lease_seconds"], 1500)
            self.assertEqual(manifest["ffmpeg_cap_seconds"], 780)
            self.assertEqual(manifest["monthly_budget_ceiling_in_azure_billing_currency"], 200.0)
            self.assertNotIn("ServiceSecret", json.dumps(manifest))
            self.assertEqual(len(manifest["candidate_sha256"]), 64)
            self.assertIn("live_exact_resource_group_contributor_iam",
                          manifest["required_external_evidence"])

    def test_missing_poison_trigger_blocks_zip_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            params = write_params(folder)
            candidate = write_test_zip(folder / "broken.zip", damage_trigger=True)
            with self.assertRaisesRegex(ValueError, "queue/poison trigger"):
                gate.prepare(params, candidate, "a" * 40, 200, first=True)

    def test_rollback_requires_distinct_prior_verified_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            params = write_params(folder)
            current = write_test_zip(folder / "current.zip")
            old = write_test_zip(folder / "old.zip", suffix=b"\n# old release\n")
            with self.assertRaises(ValueError):
                gate.prepare(params, current, "a" * 40, 200, first=False)
            with self.assertRaises(ValueError):
                gate.prepare(params, current, "a" * 40, 200, first=True,
                             previous=old)
            with self.assertRaises(ValueError):
                gate.prepare(params, current, "a" * 40, 200, first=False,
                             previous=current)
            valid = gate.prepare(params, current, "a" * 40, 200, first=False,
                                 previous=old)
            self.assertNotEqual(valid["candidate_sha256"], valid["last_good_sha256"])

    def test_offline_guard_does_not_change_azure(self):
        script = (ROOT / "scripts/deploy/release_package.py").read_text()
        for cmd in ("az deployment group create", "az functionapp deploy",
                    "az storage queue create", "supabase db push"):
            self.assertNotIn(cmd, script)
        infra = (ROOT / "scripts/deploy/apply-infra.sh").read_text()
        self.assertIn("azure-readonly-preflight.sh", infra)
        self.assertIn("--get-function-name", infra)
        self.assertIn("existing Function App", infra)
        self.assertIn("--check-parameters", (ROOT / "scripts/deploy/plan.sh").read_text())


if __name__ == "__main__":
    unittest.main()
