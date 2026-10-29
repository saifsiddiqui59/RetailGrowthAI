"""Offline inventory for actual local Faster-Whisper model weights.

Produces a DRAFT with all local SHA256 digests and pinned model revision.
Deliberately leaves commercial_rights_reviewed=false; no operator may turn
it on until independently reviewing model, voices, bundled dependencies,
redistribution and service-use terms. Never downloads or executes an AI model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from faster_whisper_cpu import LocalFasterWhisperError

REV="536b0662742c02347bc0e980a01041f333bce120"
REQUIRED=("config.json","model.bin","tokenizer.json")
OPTIONAL=("preprocessor_config.json","vocabulary.json","vocab.json",
          "tokenizer_config.json","generation_config.json")
MAX_BYTES=1024*1024*1024

def draft_actual_model_inventory(model_dir: str) -> dict:
    directory=Path(model_dir)
    if not directory.is_absolute() or not directory.is_dir() or directory.is_symlink():
        raise LocalFasterWhisperError("Approved absolute local checkpoint directory required")
    names={p.name for p in directory.iterdir()}
    if not set(REQUIRED).issubset(names) or not names.issubset(set(REQUIRED)|set(OPTIONAL)):
        raise LocalFasterWhisperError("Missing mandatory or unreviewed extra model file")
    if len(names)>8:
        raise LocalFasterWhisperError("Unbounded checkpoint inventory")
    values={}
    for name in sorted(names):
        p=directory/name
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or p.is_symlink() or not 0<st.st_size<=MAX_BYTES:
            raise LocalFasterWhisperError("Unsafe, empty, oversized or linked checkpoint")
        digest=hashlib.sha256()
        with p.open("rb") as fd:
            while chunk:=fd.read(1024*1024):
                digest.update(chunk)
        if p.stat().st_size!=st.st_size:
            raise LocalFasterWhisperError("Checkpoint changed while hashing")
        values[name]=digest.hexdigest()
    return {
        "version":"feature7_faster_whisper_model_manifest_v1",
        "model_project":"Systran/faster-whisper-small",
        "model_revision":REV,
        "commercial_rights_reviewed":False,
        "files":values
    }

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--model-dir",required=True)
    parser.add_argument("--output-file",required=True)
    args=parser.parse_args()
    try:
        manifest=draft_actual_model_inventory(args.model_dir)
        target=Path(args.output_file)
        if not target.is_absolute() or not target.parent.is_dir() or target.exists():
            raise LocalFasterWhisperError("New absolute private manifest path required")
        raw=json.dumps(manifest,indent=2,sort_keys=True)+"\n"
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as writer:
                writer.write(raw)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        print("F7 model inventory created; commercial review is FALSE; "
              "runtime will refuse to load until independently approved")
        return 0
    except (OSError,ValueError) as err:
        print("Feature7 inventory denied: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
