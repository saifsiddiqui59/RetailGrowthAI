"""Fail-closed offline audit of Feature2 Creative Director Azure runtime readiness.

The current Python Functions deployment ZIP is built separately from the Node
source checkout. It must never claim the pinned JS planner can run just because
the GitHub runner itself has Node installed. No cloud I/O, deployment or secrets.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha1, sha256
from hmac import compare_digest
import re
import struct
from typing import Mapping
from zipfile import ZipFile
from .feature2_director_package import PINNED_UPSTREAM_BLOBS


REQUIRED = frozenset({
    "ai_agents/creative-director/director-cli.js",
    "ai_agents/creative-director/director.js",
    "ai_agents/creative-director/upstream/explainer-plan.js",
    "ai_agents/creative-director/upstream/explainer-cues.js",
    "ai_agents/creative-director/upstream/explainer-revise.js",
    "ai_agents/creative-director/upstream/music-video-plan.js",
    "ai_agents/creative-director/upstream/LICENSE",
})
CANDIDATE_RUNTIME = "bin/node"
MAX_NODE_BYTES = 180 * 1024 * 1024
SHA256_HEX = re.compile(r"[a-f0-9]{64}")

def _node_binary_attested(payload: bytes, expected_sha256: str | None) -> bool:
    """Offline structure+digest check; independently executed Azure Node22
    and approved library compatibility remain separate operator evidence.
    """
    if (not isinstance(payload, bytes) or not 100_000 <= len(payload) <= MAX_NODE_BYTES
            or not isinstance(expected_sha256, str)
            or SHA256_HEX.fullmatch(expected_sha256) is None):
        return False
    if (len(payload) < 64 or payload[:7] != b"\x7fELF\x02\x01\x01"
            or struct.unpack_from("<H", payload, 18)[0] != 62):
        return False
    # A magic prefix and x86_64 machine ID alone also match forged ELF-like
    # blobs. Check the ELF64 executable/shared-object header and an executable
    # PT_LOAD segment before consulting the independently approved digest.
    e_type, e_machine, e_version = struct.unpack_from("<HHI", payload, 16)
    e_ehsize = struct.unpack_from("<H", payload, 52)[0]
    if e_type not in (2, 3) or e_machine != 62 or e_version != 1 or e_ehsize != 64:
        return False
    phoff = struct.unpack_from("<Q", payload, 32)[0]
    phentsize, phnum = struct.unpack_from("<HH", payload, 54)
    if not phoff or phentsize < 56 or not 1 <= phnum <= 1024:
        return False
    if phoff + phentsize * phnum > len(payload):
        return False
    if not any(
        struct.unpack_from("<I", payload, phoff + n * phentsize)[0] == 1
        and struct.unpack_from("<I", payload, phoff + n * phentsize + 4)[0] & 1
        for n in range(phnum)
    ):
        return False
    return compare_digest(sha256(payload).hexdigest(), expected_sha256)
PIN = "4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f"


@dataclass(frozen=True)
class RuntimeAudit:
    ready_to_enable: bool
    missing_code: tuple[str, ...]
    node_runtime_verified: bool
    license_verified: bool
    blocking_reasons: tuple[str, ...]


def audit_entries(
    entries: Mapping[str, bytes],
    *,
    runtime_linux_node22_verified: bool = False,
    operator_approved_runtime: bool = False,
    approved_node_sha256: str | None = None,
) -> RuntimeAudit:
    """Only a verified Linux Node22+ deployed runtime can pass, not CI PATH."""
    if not isinstance(entries, Mapping):
        raise TypeError("Trusted ZIP entry map required")
    keys = set(entries)
    missing = tuple(sorted(REQUIRED - keys))
    pinned_prefix = "ai_agents/creative-director/"
    originals_ok = all(
        isinstance(entries.get(pinned_prefix + name), bytes)
        and compare_digest(
            sha1(b"blob " + str(len(entries[pinned_prefix + name])).encode("ascii")
                 + b"\0" + entries[pinned_prefix + name]).hexdigest(), expected
        )
        for name, expected in PINNED_UPSTREAM_BLOBS.items()
    )
    license_bytes = entries.get("ai_agents/creative-director/upstream/LICENSE")
    license_ok = isinstance(license_bytes, bytes) and (
        b"MIT License" in license_bytes and b"Copyright (c) 2026 Kuble AG" in license_bytes
    )
    # Existing zip's chmod helper only sets execute bit for ffmpeg/ffprobe.
    # Node presence alone is NOT runnable evidence: require separate signed
    # Linux ELF/architecture, node version, permissions and init PATH audit.
    has_node = CANDIDATE_RUNTIME in keys
    node_attested = _node_binary_attested(entries.get(CANDIDATE_RUNTIME),
                                          approved_node_sha256) if has_node else False
    node_ok = bool(runtime_linux_node22_verified and operator_approved_runtime
                   and has_node and node_attested)
    reasons: list[str] = []
    if missing:
        reasons.append("PINNED_DIRECTOR_SOURCE_NOT_PACKAGED")
    if not license_ok:
        reasons.append("PINNED_MIT_NOTICE_NOT_PACKAGED")
    if not originals_ok:
        reasons.append("PINNED_DIRECTOR_UPSTREAM_HASH_MISMATCH")
    if not has_node:
        reasons.append("NODE_RUNTIME_NOT_IN_FUNCTION_ZIP")
    elif not node_attested:
        reasons.append("NODE_RUNTIME_BINARY_NOT_ATTESTED")
    if not runtime_linux_node22_verified or not operator_approved_runtime:
        reasons.append("DEPLOYED_LINUX_NODE22_RUNTIME_UNVERIFIED")
    return RuntimeAudit(not reasons, missing, node_ok, license_ok, tuple(reasons))


def audit_zip(path: str, *, runtime_linux_node22_verified=False,
              operator_approved_runtime=False,
              approved_node_sha256: str | None = None) -> RuntimeAudit:
    """Bounded offline ZIP audit. Never executes or downloads an arbitrary Node."""
    with ZipFile(path) as z:
        infos = z.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)) or len(names) > 200:
            raise ValueError("Unsafe duplicate or oversized runtime manifest")
        if sum(info.file_size for info in infos) > 400 * 1024 * 1024:
            raise ValueError("Oversized unpacked runtime ZIP")
        for info in infos:
            name = info.filename
            if (name.startswith("/") or ".." in name.split("/")
                    or "\\" in name or name.startswith(".")):
                raise ValueError("Unsafe runtime ZIP member")
            if name == CANDIDATE_RUNTIME:
                if not 100_000 <= info.file_size <= MAX_NODE_BYTES:
                    raise ValueError("Invalid Node executable size")
                if not (info.external_attr >> 16) & 0o111:
                    raise ValueError("Node executable permission absent")
            elif name in REQUIRED and info.file_size > 250_000:
                raise ValueError("Oversized Creative Director source")
        selected = REQUIRED | {CANDIDATE_RUNTIME}
        members = {name: z.read(name) for name in selected if name in names}
    return audit_entries(
        members,
        runtime_linux_node22_verified=runtime_linux_node22_verified,
        operator_approved_runtime=operator_approved_runtime,
        approved_node_sha256=approved_node_sha256,
    )
