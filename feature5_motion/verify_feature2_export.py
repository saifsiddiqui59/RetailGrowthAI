"""GPU-off CLI boundary for authentic Feature2 Creative Director JSON export.

Example after Feature2 PR #551 integration:
    node ai-agents/creative-director/export-feature4-feature5-fixture.js 30 |
        python -m feature5_motion.verify_feature2_export --duration 30

Read the actual exported stdout, never a reconstructed first-party mock.
This validates editorial identity and continuity only: no inference, billing,
current customer media grant, authorized first frame, or publishing.
"""
from __future__ import annotations

import argparse
import json
import sys

from .feature2_storyboard_bridge import qualify_feature2_offline_storyboard
from .wan22_motion_adapter import WanCompatibilityError

MAX_INPUT_BYTES = 2 * 1024 * 1024


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate editorial JSON object key")
        result[key] = value
    return result


def qualify_export_bytes(raw: bytes, *, duration: int) -> dict:
    """Consume bounded, unambiguous original exporter bytes, without trust promotion."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_INPUT_BYTES:
        raise WanCompatibilityError("Missing or oversized Feature2 source JSON")
    if type(duration) is not int or duration not in (15, 30, 60):
        raise WanCompatibilityError("Invalid expected editorial duration")
    try:
        packet = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys,
                            parse_constant=lambda _: (_ for _ in ()).throw(
                                ValueError("Non-finite JSON number")))
    # JSON parser recursion errors are untrusted-input rejection, not a CLI crash.
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError) as exc:
        raise WanCompatibilityError("Invalid or ambiguous Feature2 source JSON") from exc
    if type(packet) is not dict or packet.get("duration_seconds") != duration:
        raise WanCompatibilityError("Feature2 duration differs from invocation")
    receipt = qualify_feature2_offline_storyboard(packet)
    if (receipt["duration_seconds"] != duration
            or receipt["segment_count"] != duration // 5
            or receipt["status"] != "SOURCE_ONLY_NOT_AUTHORIZED_FOR_INFERENCE"
            or receipt["can_submit_provider"] is not False
            or receipt["can_publish"] is not False):
        raise WanCompatibilityError("Editorial source cannot authorize model execution")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a GPU-OFF Feature2 JSON export")
    parser.add_argument("--duration", required=True, type=int, choices=(15, 30, 60))
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        receipt = qualify_export_bytes(raw, duration=args.duration)
    except (WanCompatibilityError, OSError):
        sys.stderr.write("Feature2 source rejected; no GPU/provider call or media output.\n")
        return 2
    sys.stdout.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
