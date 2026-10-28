"""Fail-closed offline audit of Feature2 Creative Director Azure runtime readiness.

The current Python Functions deployment ZIP is built separately from the Node
source checkout. It must never claim the pinned JS planner can run just because
the GitHub runner itself has Node installed. No cloud I/O, deployment or secrets.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Mapping
from zipfile import ZipFile


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
) -> RuntimeAudit:
    """Only a verified Linux Node22+ deployed runtime can pass, not CI PATH."""
    if not isinstance(entries, Mapping):
        raise TypeError("Trusted ZIP entry map required")
    keys = set(entries)
    missing = tuple(sorted(REQUIRED - keys))
    license_bytes = entries.get("ai_agents/creative-director/upstream/LICENSE")
    license_ok = isinstance(license_bytes, bytes) and (
        b"MIT License" in license_bytes and b"Copyright (c) 2026 Kuble AG" in license_bytes
    )
    # Existing zip's chmod helper only sets execute bit for ffmpeg/ffprobe.
    # Node presence alone is NOT runnable evidence: require separate signed
    # Linux ELF/architecture, node version, permissions and init PATH audit.
    has_node = CANDIDATE_RUNTIME in keys
    node_ok = bool(runtime_linux_node22_verified and operator_approved_runtime and has_node)
    reasons: list[str] = []
    if missing:
        reasons.append("PINNED_DIRECTOR_SOURCE_NOT_PACKAGED")
    if not license_ok:
        reasons.append("PINNED_MIT_NOTICE_NOT_PACKAGED")
    if not has_node:
        reasons.append("NODE_RUNTIME_NOT_IN_FUNCTION_ZIP")
    if not runtime_linux_node22_verified or not operator_approved_runtime:
        reasons.append("DEPLOYED_LINUX_NODE22_RUNTIME_UNVERIFIED")
    return RuntimeAudit(not reasons, missing, node_ok, license_ok, tuple(reasons))


def audit_zip(path: str, *, runtime_linux_node22_verified=False,
              operator_approved_runtime=False) -> RuntimeAudit:
    """Read-only ZIP audit, bounded to required members, not a cloud release."""
    with ZipFile(path) as z:
        names = set(z.namelist())
        if len(names) != len(z.namelist()) or len(names) > 200:
            raise ValueError("Unsafe duplicated or oversized runtime manifest")
        members = {name: z.read(name) for name in REQUIRED & names}
        if CANDIDATE_RUNTIME in names:
            # Binary content intentionally not inspected or executed by this audit.
            members[CANDIDATE_RUNTIME] = b"present-not-verified"
    return audit_entries(
        members,
        runtime_linux_node22_verified=runtime_linux_node22_verified,
        operator_approved_runtime=operator_approved_runtime,
    )
