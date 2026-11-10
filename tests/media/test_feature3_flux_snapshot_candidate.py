"""No model download/GPU: real SHA256 over small synthetic snapshot fixture."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from flux_t4_snapshot import REQUIRED_CONFIG_FILES,verify_reviewed_flux_snapshot
from flux_t4_review_candidate import build_review_candidate,write_candidate
from ai_providers_v2 import ProviderBlocked

SHARDS=(
 "text_encoder/model-00001-of-00002.safetensors",
 "text_encoder/model-00002-of-00002.safetensors",
 "transformer/diffusion_pytorch_model.safetensors",
 "vae/diffusion_pytorch_model.safetensors",
)

def fake_snapshot(root):
    root.mkdir()
    for name in sorted(REQUIRED_CONFIG_FILES | set(SHARDS)):
        target=root/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(("fixture-"+name).encode())
    (root/"model_index.json").write_text('{"_class_name":"Flux2KleinPipeline"}')
    return root

class CandidateTests(unittest.TestCase):
    def test_manifest_hashes_all_files_but_never_auto_approves(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            weights=fake_snapshot(root/"weights")
            dest=root/"review"/"candidate.json"
            saved=write_candidate(weights,dest)
            self.assertEqual(saved,dest)
            data=json.loads(dest.read_text())
            self.assertFalse(data["dependencies_operator_approved"])
            self.assertEqual(set(data["configs_sha256"]),set(REQUIRED_CONFIG_FILES))
            self.assertEqual(set(data["shards_sha256"]),set(SHARDS))
            self.assertEqual(len(data["model_index_sha256"]),64)
            self.assertEqual(dest.stat().st_mode & 0o777,0o600)
            with self.assertRaises(ProviderBlocked):
                verify_reviewed_flux_snapshot(weights,dest)
            with self.assertRaises(ProviderBlocked):
                write_candidate(weights,dest)
    def test_any_absent_file_or_invalid_index_fails_closed(self):
        with TemporaryDirectory() as td:
            root=Path(td);weights=fake_snapshot(root/"weights")
            (weights/"tokenizer/tokenizer.json").unlink()
            with self.assertRaises(ProviderBlocked):build_review_candidate(weights)
        with TemporaryDirectory() as td:
            root=Path(td);weights=fake_snapshot(root/"weights")
            (weights/"model_index.json").write_text('{"_class_name":"OtherPipeline"}')
            with self.assertRaises(ProviderBlocked):build_review_candidate(weights)
    def test_symlinked_shard_parent_denied_before_hash(self):
        with TemporaryDirectory() as td:
            root=Path(td);weights=fake_snapshot(root/"weights")
            directory=weights/"text_encoder"
            outside=root/"outside"
            directory.rename(outside)
            directory.symlink_to(outside,target_is_directory=True)
            with self.assertRaises(ProviderBlocked):build_review_candidate(weights)
    def test_candidate_inside_snapshot_or_existing_path_denied(self):
        with TemporaryDirectory() as td:
            root=Path(td);weights=fake_snapshot(root/"weights")
            with self.assertRaises(ProviderBlocked):
                write_candidate(weights,weights/"candidate.json")
            with self.assertRaises(ProviderBlocked):
                write_candidate(weights,root/"weights"/"already-here.json")
            with self.assertRaises(ProviderBlocked):
                write_candidate(weights,Path("relative-candidate.json"))
    def test_no_gpu_or_network_dependency(self):
        source=(Path(__file__).resolve().parents[2]/"poster-engine/flux_t4_review_candidate.py").read_text()
        self.assertNotIn("from_pretrained",source)
        self.assertNotIn("torch.cuda",source)
        self.assertNotIn("huggingface_hub",source)

if __name__=="__main__":unittest.main()
