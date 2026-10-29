"""Synthetic fake wheels for protocol ONLY; no dependency installation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED

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


    def rewrite_wheel(self, name, version, metadata, extra=None):
        """Re-pin mutation bytes, proving the archive audit is not just SHA."""
        filename=f"{name.replace('-','_')}-{version}-py3-none-any.whl"
        p=self.root/filename
        with ZipFile(p,"w",compression=ZIP_DEFLATED) as z:
            z.writestr(f"{name.replace('-','_')}-{version}.dist-info/METADATA",
                       metadata)
            if extra is not None:
                z.writestr(extra[0],extra[1])
        row=next(r for r in self.wheels if r["distribution"]==name)
        row["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.save()

    def test_repin_wrong_filename_and_unlisted_extra_wheel_denied(self):
        self.wheels[0]["distribution"]="foreign-whisper"
        self.save()
        with self.assertRaisesRegex(WheelhouseRejected,"filename identity"):
            audit_wheelhouse(str(self.root),str(self.manifest))
        self.wheels[0]["distribution"]="faster-whisper"
        self.save()
        extra=self.root/"unlisted-1.0-py3-none-any.whl"
        extra.write_bytes(b"unapproved")
        with self.assertRaisesRegex(WheelhouseRejected,"Unlisted"):
            audit_wheelhouse(str(self.root),str(self.manifest))

    def test_repin_oversized_metadata_and_zip_symlink_denied(self):
        name="faster-whisper"
        metadata="Metadata-Version: 2.1\nName: faster-whisper\nVersion: 1.2.1\n"
        self.rewrite_wheel(name,"1.2.1",metadata+"X-Note: "+"x"*270000+"\n")
        with self.assertRaisesRegex(WheelhouseRejected,"metadata exceeds budget"):
            audit_wheelhouse(str(self.root),str(self.manifest))
        archive=self.root/"faster_whisper-1.2.1-py3-none-any.whl"
        with ZipFile(archive,"w") as z:
            z.writestr("faster_whisper-1.2.1.dist-info/METADATA",metadata)
            link=ZipInfo("foo-link")
            link.create_system=3
            link.external_attr=(0o120777 << 16)
            z.writestr(link,"../secret")
        self.wheels[0]["sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
        self.save()
        with self.assertRaisesRegex(WheelhouseRejected,"symlink"):
            audit_wheelhouse(str(self.root),str(self.manifest))

    def test_repin_wrong_dist_info_and_malformed_requirement_denied(self):
        base="Metadata-Version: 2.1\nName: faster-whisper\nVersion: 1.2.1\n"
        p=self.root/"faster_whisper-1.2.1-py3-none-any.whl"
        with ZipFile(p,"w") as z:
            z.writestr("ctranslate2-1.2.1.dist-info/METADATA",base)
        self.wheels[0]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.save()
        with self.assertRaisesRegex(WheelhouseRejected,"Dist-info"):
            audit_wheelhouse(str(self.root),str(self.manifest))
        self.rewrite_wheel("faster-whisper","1.2.1",base+
                           "Requires-Dist: ???\n")
        with self.assertRaisesRegex(WheelhouseRejected,"Malformed"):
            audit_wheelhouse(str(self.root),str(self.manifest))

    def test_manifest_must_be_json_object(self):
        self.manifest.write_text('[]')
        with self.assertRaises(WheelhouseRejected):
            audit_wheelhouse(str(self.root),str(self.manifest))


    def test_repin_incompatible_transitive_version_is_denied(self):
        base="Metadata-Version: 2.1\\nName: faster-whisper\\nVersion: 1.2.1\\n"
        self.rewrite_wheel("faster-whisper","1.2.1",base+
                           "Requires-Dist: ctranslate2>=5.0,<6.0\\n")
        with self.assertRaisesRegex(WheelhouseRejected,"version violates"):
            audit_wheelhouse(str(self.root),str(self.manifest))

    def test_compatible_numeric_version_range_and_marker_are_conservative(self):
        base="Metadata-Version: 2.1\\nName: faster-whisper\\nVersion: 1.2.1\\n"
        self.rewrite_wheel("faster-whisper","1.2.1",base+
                           'Requires-Dist: ctranslate2 (>=4.0,<5.0); python_version >= "3.9"\\n')
        out=audit_wheelhouse(str(self.root),str(self.manifest))
        self.assertTrue(out["conservative_numeric_dependency_constraints_checked"])
        self.assertFalse(out["platform_abi_tested"])
        self.assertFalse(out["approved_for_deployment"])

    def test_direct_url_or_trailing_unparsed_dependency_syntax_denied(self):
        base="Metadata-Version: 2.1\\nName: faster-whisper\\nVersion: 1.2.1\\n"
        for req in ("ctranslate2 @ https://invalid.example/evil.whl",
                    "ctranslate2>=4.0 unexpected", "ctranslate2==4.7.0"):
            self.rewrite_wheel("faster-whisper","1.2.1",base+
                               f"Requires-Dist: {req}\\n")
            with self.assertRaises(WheelhouseRejected, msg=req):
                audit_wheelhouse(str(self.root),str(self.manifest))

if __name__=="__main__":unittest.main()
