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
DEP=re.compile(r"^\s*([A-Za-z0-9_.-]+)(?=\s|\[|[<>=!~(;]|$)")
MAX_MEMBERS=10000
MAX_METADATA_BYTES=256*1024
MAX_UNPACKED_BYTES=2*1024*1024*1024

def normal(name):return re.sub(r"[-_.]+","-",name).lower()

# This is deliberately a conservative numeric subset of PEP 508/440. It
# rejects unsupported requirement syntax rather than treating a dependency
# name alone as proof that a conflicting pinned wheel is installable.
SPEC = re.compile(r"(~=|==|!=|<=|>=|<|>)\s*([0-9]+(?:\.[0-9]+)*)")
SPEC_LIST = re.compile(
    r"(?:~=|==|!=|<=|>=|<|>)\s*[0-9]+(?:\.[0-9]+)*"
    r"(?:\s*,\s*(?:~=|==|!=|<=|>=|<|>)\s*[0-9]+(?:\.[0-9]+)*)*"
)
REQ_NAME = re.compile(
    r"\s*([A-Za-z0-9][A-Za-z0-9_.-]{0,99})"
    r"(?:\[[A-Za-z0-9_,.-]+\])?\s*(.*?)\s*"
)

def parse_requirement(value):
    if not isinstance(value,str) or len(value)>512 or any(
        ch in value for ch in ("\n","\r","\x00","@")
    ):
        raise WheelhouseRejected("Unsupported or unsafe declared dependency")
    base, separator, marker = value.partition(";")
    # Marker evaluation is intentionally NOT asserted. All marker-qualified
    # dependencies must still be present, even when not needed on this host.
    if separator and (not marker.strip() or
                      re.fullmatch(r"[A-Za-z0-9_.!<>=(),'\\" \t-]+",marker) is None):
        raise WheelhouseRejected("Unsupported dependency environment marker")
    match = REQ_NAME.fullmatch(base)
    if not match:
        raise WheelhouseRejected("Malformed declared dependency")
    name, specs = match.groups()
    specs = specs.strip()
    if specs.startswith("(") and specs.endswith(")"):
        specs = specs[1:-1].strip()
    if specs and SPEC_LIST.fullmatch(specs) is None:
        raise WheelhouseRejected("Unsupported dependency version constraint")
    return normal(name), SPEC.findall(specs)

def satisfies_numeric_spec(version, operator, required):
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)*",version) is None:
        raise WheelhouseRejected("Unsupported pinned dependency version")
    current = tuple(int(p) for p in version.split("."))
    target = tuple(int(p) for p in required.split("."))
    width = max(len(current),len(target))
    left = current + (0,)*(width-len(current))
    right = target + (0,)*(width-len(target))
    if operator == "~=":
        if len(target)<2:
            raise WheelhouseRejected("Invalid compatible-version constraint")
        upper = list(target[:-1])
        upper[-1] += 1
        bound = tuple(upper)+(0,)*(width-len(upper))
        return left >= right and left < bound
    return {"==":left==right,"!=":left!=right,">=":left>=right,
            "<=":left<=right,">":left>right,"<":left<right}[operator]

def wheel_file_identity(filename, distribution, version):
    """Strict PEP 427 filename envelope; not an ABI/install approval."""
    if not isinstance(filename,str) or not filename.endswith(".whl"):
        raise WheelhouseRejected("Invalid wheel filename")
    segments=filename[:-4].split("-")
    if len(segments) not in (5,6):
        raise WheelhouseRejected("Wheel filename must contain distribution/version/tags")
    disk_name,disk_version=segments[:2]
    if normal(disk_name)!=normal(distribution) or disk_version!=version or (
        len(segments)==6 and not re.fullmatch(r"[0-9][A-Za-z0-9_]*",segments[2])
    ):
        raise WheelhouseRejected("Wheel filename identity does not match pinned inventory")
    if any(not x or re.fullmatch(r"[A-Za-z0-9_.]+",x) is None for x in segments[3 if len(segments)==6 else 2:]):
        raise WheelhouseRejected("Unsafe or invalid wheel compatibility tags")

def safe_metadata(z, distribution, version):
    """Verify the ZIP structure without decompressing unbounded metadata."""
    entries=z.infolist()
    if not entries or len(entries)>MAX_MEMBERS:
        raise WheelhouseRejected("Unbounded or empty wheel ZIP")
    seen=set()
    expanded=0
    metadata=[]
    for info in entries:
        name=info.filename
        if (name in seen or name.startswith("/") or "\\" in name or
            "\x00" in name or any(p in ("", ".", "..") for p in name.rstrip("/").split("/"))):
            raise WheelhouseRejected("Duplicate or unsafe wheel ZIP member")
        seen.add(name)
        mode=info.external_attr >> 16
        if stat.S_IFMT(mode)==stat.S_IFLNK:
            raise WheelhouseRejected("Wheel ZIP symlink forbidden")
        expanded+=info.file_size
        if expanded>MAX_UNPACKED_BYTES or (
            info.file_size>MAX_METADATA_BYTES and name.endswith(".dist-info/METADATA")
        ):
            raise WheelhouseRejected("Wheel ZIP expansion or metadata exceeds budget")
        if name.endswith(".dist-info/METADATA"):
            metadata.append(info)
    if len(metadata)!=1:
        raise WheelhouseRejected("Missing or ambiguous wheel package metadata")
    meta=metadata[0]
    prefix=meta.filename.split("/")[0]
    if (meta.filename!=prefix+"/METADATA" or
        not prefix.endswith(".dist-info") or
        prefix[:-10].replace("_","-").lower()!=
          (distribution.replace("_","-")+"-"+version).lower()):
        raise WheelhouseRejected("Dist-info directory does not match wheel identity")
    if meta.file_size>MAX_METADATA_BYTES:
        raise WheelhouseRejected("Metadata too large to inspect")
    return Parser().parsestr(z.read(meta).decode("utf-8"))


def audit_wheelhouse(folder: str,manifest_file: str)->dict:
    root=Path(folder);manifest=Path(manifest_file)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink() or \
       not manifest.is_absolute() or not manifest.is_file() or manifest.is_symlink():
        raise WheelhouseRejected("Absolute local wheelhouse and manifest required")
    if manifest.stat().st_size>128*1024:
        raise WheelhouseRejected("Excessive operator manifest")
    data=json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data,dict):
        raise WheelhouseRejected("Operator wheelhouse JSON object required")
    rows=data.get("wheels")
    if data.get("schema")!="feature7_cpu_wheelhouse_v1" or not isinstance(rows,list) \
       or not 2<=len(rows)<=96:
        raise WheelhouseRejected("Operator pinned wheelhouse inventory required")
    names=set();files=set();references={};versions={}
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"filename","distribution","version","sha256"}:
            raise WheelhouseRejected("Exact wheel inventory shape required")
        name=row["distribution"];version=row["version"];filename=row["filename"]
        if not isinstance(name,str) or NAME.fullmatch(name) is None or \
           not isinstance(version,str) or not re.fullmatch(r"[0-9][A-Za-z0-9.+_-]{0,60}",version) or \
           not isinstance(filename,str) or re.fullmatch(r"[A-Za-z0-9_.+-]+\.whl",filename) is None or \
           not isinstance(row["sha256"],str) or SHA.fullmatch(row["sha256"]) is None:
            raise WheelhouseRejected("Untrusted wheel name, version or digest")
        wheel_file_identity(filename,name,version)
        key=normal(name)
        if key in names or filename in files:
            raise WheelhouseRejected("Conflicting or duplicate wheel distribution")
        names.add(key);files.add(filename);versions[key]=version
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
                msg=safe_metadata(z,name,version)
        except (BadZipFile,UnicodeDecodeError,RuntimeError) as exc:
            raise WheelhouseRejected("Unreadable wheel metadata") from exc
        if normal(msg.get("Name",""))!=key or msg.get("Version")!=version:
            raise WheelhouseRejected("Wheel identity metadata mismatch")
        references[key]=[]
        for requirement in msg.get_all("Requires-Dist",[]):
            references[key].append(parse_requirement(requirement))
    if {p.name for p in root.iterdir() if p.name.endswith(".whl")}!=files:
        raise WheelhouseRejected("Unlisted or extra wheel in operator directory")
    if "faster-whisper" not in names or "ctranslate2" not in names:
        raise WheelhouseRejected("Actual pinned Faster-Whisper and CTranslate2 wheels required")
    target=next(r for r in rows if normal(r["distribution"])=="faster-whisper")
    if target["version"]!="1.2.1":
        raise WheelhouseRejected("Faster-Whisper worker requires pinned version 1.2.1")
    missing=sorted({dep for required in references.values()
                    for dep,_ in required if dep not in names})
    if missing:
        raise WheelhouseRejected("Transitive dependencies not pinned in offline wheelhouse: "+", ".join(missing[:12]))
    for required in references.values():
        for dep,specs in required:
            if not all(satisfies_numeric_spec(versions[dep],op,v)
                       for op,v in specs):
                raise WheelhouseRejected("Pinned dependency version violates declared constraint: "+dep)
    return {
      "schema":"feature7_cpu_wheelhouse_audit_v1",
      "sha256_verified_wheel_files":len(rows),
      "declared_transitive_requirement_names_present":True,
      "conservative_numeric_dependency_constraints_checked":True,
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
