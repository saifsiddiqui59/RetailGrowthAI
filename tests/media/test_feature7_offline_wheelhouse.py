"""Synthetic fake wheels for protocol ONLY; no dependency installation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"video-engine"/"feature7"))
from offline_wheelhouse_audit import audit_wheelhouse,WheelhouseRejected

class OfflineWheelhouseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="f7-wheels-contract-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.wheels=[]
        self.write_wheel("faster-whisper","1.2.1",["ctranslate2"])
        self.write_wheel("ctranslate2","4.6.0",[])
        self.manifest=self.root/"operator.json"
        self.save()

    def write_wheel(self,name,version,requires):
        filename=f"{name.replace('-','_')}-{version}-py3-none-any.whl"
        file=self.root/filename
        with ZipFile(file,"w") as z:
            data=f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"+\
                "".join(f"Requires-Dist: {x}\n" for x in requires)
            z.writestr(f"{name.replace('-','_')}-{version}.dist-info/METADATA",data)
        self.wheels.append({"filename":filename,"distribution":name,
          "version":version,"sha256":hashlib.sha256(file.read_bytes()).hexdigest()})

    def save(self):
        self.manifest.write_text(json.dumps({
          "schema":"feature7_cpu_wheelhouse_v1","wheels":self.wheels}))

    def test_test_only_pinned_wheel_closure_never_claims_runtime_or_license(self):
        out=audit_wheelhouse(str(self.root),str(self.manifest))
        self.assertEqual(out["sha256_verified_wheel_files"],2)
        self.assertFalse(out["platform_abi_tested"])
        self.assertFalse(out["approved_for_deployment"])
        self.assertFalse(out["model_weights_loaded"])

    def test_unlisted_dependency_or_tamper_is_denied(self):
        self.wheels.clear()
        for p in self.root.glob("*.whl"):p.unlink()
        self.write_wheel("faster-whisper","1.2.1",["ctranslate2","tokenizers"])
        self.write_wheel("ctranslate2","4.6.0",[])
        self.save()
        with self.assertRaises(WheelhouseRejected):
            audit_wheelhouse(str(self.root),str(self.manifest))
        self.wheels.clear()
        for p in self.root.glob("*.whl"):p.unlink()
        self.write_wheel("faster-whisper","1.2.1",["ctranslate2"])
        self.write_wheel("ctranslate2","4.6.0",[])
        self.save()
        (self.root/self.wheels[0]["filename"]).write_bytes(b"tampered")
        with self.assertRaises(WheelhouseRejected):
            audit_wheelhouse(str(self.root),str(self.manifest))

if __name__=="__main__":unittest.main()
