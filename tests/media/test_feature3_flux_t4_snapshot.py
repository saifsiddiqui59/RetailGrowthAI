"""Snapshot hashes and job safety without downloading model or calling GPU."""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from PIL import Image
from io import BytesIO

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from flux_t4_snapshot import verify_reviewed_flux_snapshot,SCHEMA,OFFICIAL_REVISION,REQUIRED_CONFIG_FILES
from flux_t4_container_entrypoint import run_one, _verify_one_shot_budget
from ai_providers_v2 import ProviderBlocked

BUDGET={"RETAIL_FLUX_PAID_ONE_SHOT_APPROVED":"1",
 "RETAIL_FLUX_TOTAL_RATE_USD_PER_SECOND":"0.00001",
 "RETAIL_FLUX_MAX_USD_PER_RUN":"0.01"}
SHARDS=(
 "text_encoder/model-00001-of-00002.safetensors",
 "text_encoder/model-00002-of-00002.safetensors",
 "transformer/diffusion_pytorch_model.safetensors",
 "vae/diffusion_pytorch_model.safetensors",
)
def sha(b):return hashlib.sha256(b).hexdigest()
class FullSnapshotTests(unittest.TestCase):
 def make(self,root):
  folder=root/"weights";folder.mkdir()
  hashes={}
  for i,n in enumerate(SHARDS):
   p=folder/n;p.parent.mkdir(parents=True,exist_ok=True)
   content=("synthetic-not-real-shard-%s"%i).encode()
   p.write_bytes(content)
   hashes[n]=sha(content)
  config_hashes={}
  for i,name in enumerate(sorted(REQUIRED_CONFIG_FILES)):
   target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
   data=(f"synthetic-reviewed-config-{i}".encode())
   target.write_bytes(data)
   config_hashes[name]=sha(data)
  data=b'{"_class_name":"Flux2KleinPipeline"}'
  (folder/"model_index.json").write_bytes(data)
  manifest={
   "schema":SCHEMA,"repository":"black-forest-labs/FLUX.2-klein-4B",
   "revision_sha":OFFICIAL_REVISION,"weights_license":"Apache-2.0",
   "model_index_sha256":sha(data),"shards_sha256":hashes,
   "configs_sha256":config_hashes, "dependencies_operator_approved":True
  }
  manifest_path=root/"approval.json"
  manifest_path.write_text(json.dumps(manifest))
  return folder,manifest_path,manifest
 def test_all_synthetic_shards_accepted_but_cannot_publish(self):
  with TemporaryDirectory() as td:
   path,manifest,_=self.make(Path(td))
   result=verify_reviewed_flux_snapshot(path,manifest)
   self.assertTrue(result["weight_shards_sha256_verified"])
   self.assertFalse(result["saas_deployment_authorized"])
 def test_modified_or_missing_shard_rejected(self):
  with TemporaryDirectory() as td:
   path,manifest,_=self.make(Path(td))
   (path/SHARDS[2]).write_bytes(b"tampered")
   with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
  with TemporaryDirectory() as td:
   path,manifest,_=self.make(Path(td))
   (path/SHARDS[1]).unlink()
   with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
 def test_duplicate_approval_and_index_keys_fail_closed(self):
  # Last-key-wins JSON is ambiguous evidence, even if the final value looks safe.
  with TemporaryDirectory() as td:
   path,manifest,_=self.make(Path(td))
   original=manifest.read_text()
   self.assertIn('"dependencies_operator_approved": true',original)
   manifest.write_text(original.replace(
    '"dependencies_operator_approved": true',
    '"dependencies_operator_approved": false, "dependencies_operator_approved": true'))
   with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
  with TemporaryDirectory() as td:
   path,manifest,data=self.make(Path(td))
   index=path/"model_index.json"
   index.write_bytes(b'{"_class_name":"WrongPipeline","_class_name":"Flux2KleinPipeline"}')
   data["model_index_sha256"]=sha(index.read_bytes())
   manifest.write_text(json.dumps(data))
   with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
   from flux_t4_review_candidate import build_review_candidate
   with self.assertRaises(ProviderBlocked):build_review_candidate(path)
 def test_missing_or_replaced_tokenizer_and_scheduler_rejected(self):
  for name in ("tokenizer/tokenizer.json","scheduler/scheduler_config.json"):
   with TemporaryDirectory() as td:
    path,manifest,_=self.make(Path(td))
    (path/name).write_bytes(b"tampered")
    with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
   with TemporaryDirectory() as td:
    path,manifest,_=self.make(Path(td))
    (path/name).unlink()
    with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
 def test_parent_symlink_escape_rejected(self):
  with TemporaryDirectory() as td:
   path,manifest,_=self.make(Path(td))
   origin=path/"text_encoder"
   relocated=Path(td)/"outside"
   origin.rename(relocated)
   origin.symlink_to(relocated,target_is_directory=True)
   with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
 def test_old_partial_manifest_cannot_claim_full_snapshot(self):
  with TemporaryDirectory() as td:
   path,manifest,data=self.make(Path(td))
   data.pop("configs_sha256")
   data["schema"]="retailgrowth.flux2-klein-4b.full-snapshot.v2"
   manifest.write_text(json.dumps(data))
   with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
 def test_forbid_different_weights_license_or_revision(self):
  for field,value in (("revision_sha","f"*40),("weights_license","NON-COMMERCIAL"),("dependencies_operator_approved",False)):
   with TemporaryDirectory() as td:
    path,manifest,data=self.make(Path(td));data[field]=value
    manifest.write_text(json.dumps(data))
    with self.assertRaises(ProviderBlocked):verify_reviewed_flux_snapshot(path,manifest)
 def test_run_one_synthetic_fake_still_unapproved(self):
  with TemporaryDirectory() as td:
   root=Path(td);weights,approval,_=self.make(root)
   sid=str(uuid4());jid=str(uuid4());req=root/"job.json"
   req.write_text(json.dumps({"schema":"retailgrowth.feature3.flux-single-sample.v1",
    "shop_id":sid,"job_id":jid,"capability":"human_model",
    "prompt":"Adult model showing elegant fashion product"}))
   b=BytesIO();Image.new("RGB",(64,64),"blue").save(b,"PNG")
   with patch("flux_t4_container_entrypoint.OfflineFluxKlein4B") as worker,patch.dict(os.environ,BUDGET):
    worker.return_value.return_value=b.getvalue()
    # A synthetic test image must NEVER produce "actual_cuda_verified=true".
    with self.assertRaisesRegex(ProviderBlocked, "CUDA inference has not been verified"):
     run_one(weights=weights,approval=approval,request=req,output=root/"out")
   self.assertFalse((root/"out"/"flux-unreviewed.png").exists())
   self.assertFalse((root/"out"/"unreviewed-receipt.json").exists())
 def test_image_receipt_requires_runtime_proof_not_just_valid_png(self):
  # A successful Pillow PNG is no proof of an NVIDIA GPU.
  with TemporaryDirectory() as td:
   root=Path(td);weights,approval,_=self.make(root)
   req=root/"job.json"
   req.write_text(json.dumps({"schema":"retailgrowth.feature3.flux-single-sample.v1",
     "shop_id":str(uuid4()),"job_id":str(uuid4()),"capability":"text_to_image",
     "prompt":"Synthetic adult fashion clothing campaign"}))
   with patch("flux_t4_container_entrypoint.OfflineFluxKlein4B") as worker,patch.dict(os.environ,BUDGET):
    worker.return_value.return_value=b"not-a-png"
    with self.assertRaises(ProviderBlocked):
     run_one(weights=weights,approval=approval,request=req,output=root/"out")
   self.assertFalse((root/"out"/"unreviewed-receipt.json").exists())
 def test_missing_overbudget_nonfinite_and_unpriced_gpu_spend_is_denied(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ProviderBlocked):_verify_one_shot_budget()
  for rate,cap in (("0","100"),("NaN","100"),("Infinity","100"),
                    ("0.1","1"),("0.00001","0.001"),("-1","100")):
   with patch.dict(os.environ,{**BUDGET,
       "RETAIL_FLUX_TOTAL_RATE_USD_PER_SECOND":rate,
       "RETAIL_FLUX_MAX_USD_PER_RUN":cap},clear=True):
    with self.assertRaises(ProviderBlocked):_verify_one_shot_budget()
  with patch.dict(os.environ,BUDGET,clear=True):
   self.assertEqual(_verify_one_shot_budget(),"0.00900")
 def test_docker_runtime_has_enforced_kill_deadline(self):
  docker=(Path(__file__).resolve().parents[2]/"infra/azure/feature3-flux-t4/Dockerfile").read_text()
  self.assertIn('"/usr/bin/timeout", "--signal=TERM", "--kill-after=15s", "900s"',docker)
  self.assertIn("USER 10001:10001",docker)
  self.assertIn("HF_HUB_OFFLINE=1",docker)
if __name__=="__main__":unittest.main()
