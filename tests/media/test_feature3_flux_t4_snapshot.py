"""Snapshot hashes and job safety without downloading model or calling GPU."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from PIL import Image
from io import BytesIO

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from flux_t4_snapshot import verify_reviewed_flux_snapshot,SCHEMA,OFFICIAL_REVISION
from flux_t4_container_entrypoint import run_one
from ai_providers_v2 import ProviderBlocked

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
  data=b'{"_class_name":"Flux2KleinPipeline"}'
  (folder/"model_index.json").write_bytes(data)
  manifest={
   "schema":SCHEMA,"repository":"black-forest-labs/FLUX.2-klein-4B",
   "revision_sha":OFFICIAL_REVISION,"weights_license":"Apache-2.0",
   "model_index_sha256":sha(data),"shards_sha256":hashes,
   "dependencies_operator_approved":True
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
   with patch("flux_t4_container_entrypoint.OfflineFluxKlein4B") as worker:
    worker.return_value.return_value=b.getvalue()
    result=run_one(weights=weights,approval=approval,request=req,output=root/"out")
   self.assertEqual(result["job_id"],jid)
   self.assertTrue(result["generation_executed"])
   self.assertFalse(result["commercial_publishing_allowed"])
   self.assertFalse(result["human_reviewed"])
   self.assertEqual((root/"out"/"flux-unreviewed.png").read_bytes(),b.getvalue())
   with self.assertRaises(ProviderBlocked):
    run_one(weights=weights,approval=approval,request=req,output=root/"out")
if __name__=="__main__":unittest.main()
