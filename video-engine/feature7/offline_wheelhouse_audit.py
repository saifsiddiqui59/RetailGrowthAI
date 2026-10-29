"""Feature7 CPU wheelhouse consistency preflight, no network or installation.

Reads an operator-supplied immutable SHA256 wheel manifest and the actual
offline .whl archives. Requires every declared Requires-Dist dependency to
have a pinned wheel in this exact wheelhouse; this conservative rule may
reject optional/irrelevant platform packages. Passing does NOT establish
platform ABI safety, commercial-license review or real-model inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from email.parser import Parser
from pathlib import Path
import re
import stat
import sys
from zipfile import ZipFile, BadZipFile

class WheelhouseRejected(ValueError):pass

NAME=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
SHA=re.compile(r"^[0-9a-f]{64}$")
DEP=re.compile(r"^\s*([A-Za-z0-9_.-]+)")
def normal(name):return re.sub(r"[-_.]+","-",name).lower()

def audit_wheelhouse(folder: str,manifest_file: str)->dict:
    root=Path(folder);manifest=Path(manifest_file)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink() or \
       not manifest.is_absolute() or not manifest.is_file() or manifest.is_symlink():
        raise WheelhouseRejected("Absolute local wheelhouse and manifest required")
    if manifest.stat().st_size>128*1024:
        raise WheelhouseRejected("Excessive operator manifest")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    rows=data.get("wheels") if isinstance(data,dict) else None
    if data.get("schema")!="feature7_cpu_wheelhouse_v1" or not isinstance(rows,list) \
       or not 2<=len(rows)<=96:
        raise WheelhouseRejected("Operator pinned wheelhouse inventory required")
    names=set();files=set();references={}
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"filename","distribution","version","sha256"}:
            raise WheelhouseRejected("Exact wheel inventory shape required")
        name=row["distribution"];version=row["version"];filename=row["filename"]
        if not isinstance(name,str) or NAME.fullmatch(name) is None or \
           not isinstance(version,str) or not re.fullmatch(r"[0-9][A-Za-z0-9.+_-]{0,60}",version) or \
           not isinstance(filename,str) or re.fullmatch(r"[A-Za-z0-9_.+-]+\.whl",filename) is None or \
           not isinstance(row["sha256"],str) or SHA.fullmatch(row["sha256"]) is None:
            raise WheelhouseRejected("Untrusted wheel name, version or digest")
        key=normal(name)
        if key in names or filename in files:
            raise WheelhouseRejected("Conflicting or duplicate wheel distribution")
        names.add(key);files.add(filename)
        p=root/filename
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or p.is_symlink() or \
           not 0<st.st_size<=600*1024*1024:
            raise WheelhouseRejected("Missing, linked or oversized wheel")
        digest=hashlib.sha256()
        with p.open("rb") as stream:
            while part:=stream.read(1024*1024):digest.update(part)
        if digest.hexdigest()!=row["sha256"]:
            raise WheelhouseRejected("Wheel bytes differ from operator SHA")
        try:
            with ZipFile(p) as z:
                metas=[x for x in z.namelist() if x.endswith(".dist-info/METADATA")]
                if len(metas)!=1 or len(z.namelist())>10000:
                    raise WheelhouseRejected("Missing/ambiguous wheel package metadata")
                if any(n.startswith("/") or ".." in n.split("/") for n in z.namelist()):
                    raise WheelhouseRejected("Unsafe wheel archive member")
                msg=Parser().parsestr(z.read(metas[0]).decode("utf-8"))
        except (BadZipFile,UnicodeDecodeError) as exc:
            raise WheelhouseRejected("Unreadable wheel metadata") from exc
        if normal(msg.get("Name",""))!=key or msg.get("Version")!=version:
            raise WheelhouseRejected("Wheel identity metadata mismatch")
        references[key]=[normal(m.group(1)) for v in msg.get_all("Requires-Dist",[])
                        if (m:=DEP.match(v)) is not None]
    if "faster-whisper" not in names or "ctranslate2" not in names:
        raise WheelhouseRejected("Actual pinned Faster-Whisper and CTranslate2 wheels required")
    target=next(r for r in rows if normal(r["distribution"])=="faster-whisper")
    if target["version"]!="1.2.1":
        raise WheelhouseRejected("Faster-Whisper worker requires pinned version 1.2.1")
    missing=sorted({dep for required in references.values() for dep in required if dep not in names})
    if missing:
        raise WheelhouseRejected("Transitive dependencies not pinned in offline wheelhouse: "+", ".join(missing[:12]))
    return {
      "schema":"feature7_cpu_wheelhouse_audit_v1",
      "sha256_verified_wheel_files":len(rows),
      "declared_transitive_requirement_names_present":True,
      "faster_whisper_version":"1.2.1",
      "offline_only":True,
      "platform_abi_tested":False,
      "commercial_rights_reviewed":False,
      "installed_cpu_runtime_tested":False,
      "model_weights_loaded":False,
      "approved_for_deployment":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--wheelhouse",required=True)
    p.add_argument("--manifest",required=True)
    args=p.parse_args()
    try:print(json.dumps(audit_wheelhouse(args.wheelhouse,args.manifest),sort_keys=True));return 0
    except (OSError,ValueError) as e:
        print("Feature7 wheelhouse denied: "+str(e),file=sys.stderr);return 2
if __name__=="__main__":sys.exit(main())
