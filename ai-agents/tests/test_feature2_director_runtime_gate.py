"""Actual Functions source package must reject unbundled Node director."""
import importlib.util
from hashlib import sha256
from zipfile import ZipFile, ZipInfo
import tempfile
from pathlib import Path

from ai_agents.feature2_director_runtime_gate import audit_entries, REQUIRED, PIN
from ai_agents.feature2_director_package import source_entries


def test_current_python_flex_packaging_reports_genuine_blocker():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "deploy" / "package.py"
    spec = importlib.util.spec_from_file_location("rg_f2_package_readonly", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entries = module.source_files()
    result = audit_entries(entries)
    assert not result.ready_to_enable
    assert "PINNED_DIRECTOR_SOURCE_NOT_PACKAGED" in result.blocking_reasons
    assert "NODE_RUNTIME_NOT_IN_FUNCTION_ZIP" in result.blocking_reasons
    assert "DEPLOYED_LINUX_NODE22_RUNTIME_UNVERIFIED" in result.blocking_reasons
    assert PIN == "4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f"


def test_fake_node_file_or_ci_node_cannot_claim_live_readiness():
    members = {name: b"'use strict';" for name in REQUIRED}
    members["ai_agents/creative-director/upstream/LICENSE"] = (
        b"MIT License\nCopyright (c) 2026 Kuble AG\n"
    )
    assert not audit_entries(members).ready_to_enable
    members["bin/node"] = b"fake!"
    assert not audit_entries(members).ready_to_enable
    assert not audit_entries(members, runtime_linux_node22_verified=True).ready_to_enable
    spoofed = audit_entries(members, runtime_linux_node22_verified=True,
                            operator_approved_runtime=True,
                            approved_node_sha256=sha256(b"fake!").hexdigest())
    assert not spoofed.ready_to_enable
    assert "NODE_RUNTIME_BINARY_NOT_ATTESTED" in spoofed.blocking_reasons


def test_missing_license_never_readiness():
    members = {name: b"source" for name in REQUIRED}
    members["bin/node"] = b"fake!"
    result = audit_entries(members, runtime_linux_node22_verified=True, operator_approved_runtime=True)
    assert not result.ready_to_enable
    assert "PINNED_MIT_NOTICE_NOT_PACKAGED" in result.blocking_reasons


def test_duplicate_or_unsafe_runtime_zip_rejected_before_reading_members():
    from ai_agents.feature2_director_runtime_gate import audit_zip
    import pytest
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "candidate.zip"
        with ZipFile(path, "w") as z:
            z.writestr("ai_agents/creative-director/director.js", b"original")
            z.writestr("ai_agents/creative-director/director.js", b"duplicate")
        with pytest.raises(ValueError, match="duplicate"):
            audit_zip(str(path))
        with ZipFile(path, "w") as z:
            z.writestr("../bin/node", b"evil")
        with pytest.raises(ValueError, match="Unsafe runtime ZIP member"):
            audit_zip(str(path))
        # A 121-entry archive is rejected by the real Functions package
        # verifier; the F2 preflight must never report it as acceptable.
        with ZipFile(path, "w") as z:
            for index in range(121):
                z.writestr(f"padding/{index}.txt", b"x")
        with pytest.raises(ValueError, match="oversized runtime manifest"):
            audit_zip(str(path))


def test_runtime_zip_rejects_nonexecutable_node_even_with_claimed_operator_flags():
    from ai_agents.feature2_director_runtime_gate import audit_zip
    import pytest
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "candidate.zip"
        with ZipFile(path, "w") as z:
            z.writestr("bin/node", b"fake!")
        with pytest.raises(ValueError, match="Node executable size"):
            audit_zip(str(path), runtime_linux_node22_verified=True,
                      operator_approved_runtime=True,
                      approved_node_sha256=sha256(b"fake!").hexdigest())


def test_packaged_upstream_mit_originals_are_checked_again_not_just_at_staging():
    entries = source_entries(Path(__file__).resolve().parents[2])
    assert "PINNED_DIRECTOR_UPSTREAM_HASH_MISMATCH" not in audit_entries(entries).blocking_reasons
    forged = dict(entries)
    key = "ai_agents/creative-director/upstream/explainer-cues.js"
    forged[key] += b"\\n// tampered after source staging"
    audit = audit_entries(forged)
    assert not audit.ready_to_enable
    assert "PINNED_DIRECTOR_UPSTREAM_HASH_MISMATCH" in audit.blocking_reasons


def test_structural_node_attestation_denies_elf_header_and_segment_spoofing():
    import struct
    from ai_agents.feature2_director_runtime_gate import _node_binary_attested

    # Synthetic bytes only: not a real Node runtime or approved production hash.
    fake = bytearray(100_000)
    fake[:7] = b"\x7fELF\x02\x01\x01"
    struct.pack_into("<HHI", fake, 16, 3, 62, 1)  # ET_DYN, x86_64, v1
    struct.pack_into("<Q", fake, 32, 64)  # program-header table offset
    struct.pack_into("<H", fake, 52, 64)  # ELF64 header size
    struct.pack_into("<HH", fake, 54, 56, 1)  # one 56-byte program header
    struct.pack_into("<II", fake, 64, 1, 5)  # PT_LOAD, readable + executable
    struct.pack_into("<Q", fake, 72, 128)  # file offset
    struct.pack_into("<QQ", fake, 96, 1, 1)  # p_filesz, p_memsz
    assert _node_binary_attested(bytes(fake), sha256(fake).hexdigest())
    for offset, fmt, bad in (
        (16, "<H", 0),  # no executable/shared-object ELF type
        (20, "<I", 0),  # invalid ELF version
        (52, "<H", 0),  # invalid ELF header size
        (64, "<I", 0),  # no PT_LOAD program segment
        (68, "<I", 4),  # loadable but not executable
    ):
        tampered = bytearray(fake)
        struct.pack_into(fmt, tampered, offset, bad)
        assert not _node_binary_attested(
            bytes(tampered), sha256(tampered).hexdigest()
        )
    for offset, fmt, bad in (
        (72, "<Q", len(fake) + 1),  # executable bytes start beyond file
        (72, "<Q", len(fake)),  # nonempty segment cannot start at EOF
        (96, "<Q", 0),  # empty executable load segment
        (96, "<Q", len(fake)),  # segment extends beyond signed file
        (104, "<Q", 0),  # mapped memory smaller than file bytes
    ):
        tampered = bytearray(fake)
        struct.pack_into(fmt, tampered, offset, bad)
        assert not _node_binary_attested(
            bytes(tampered), sha256(tampered).hexdigest()
        )
