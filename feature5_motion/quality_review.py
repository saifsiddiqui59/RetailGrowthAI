"""Reviewer-facing Feature5 quality gate; visual assessment is never automated.

The existing coordinator must persist this human decision with user JWT,
tenant approval permissions, immutable media hash and an audit timestamp.
Passing machine ffprobe alone NEVER results in approval for Feature4.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from uuid import UUID
from .contracts import MotionError, canonical_uuid

CATEGORIES = (
    "human_anatomy", "smooth_motion", "garment_color", "garment_pattern",
    "sleeve_and_shape", "face_consistency", "temporal_consistency",
    "background_continuity", "frame_stability", "camera_motion",
    "product_claim_accuracy",
)


@dataclass(frozen=True)
class VisualReview:
    shop_id: str
    job_id: str
    source_asset_id: str | None
    output_asset_id: str
    reviewer_user_id: str
    reviewed_sha256: str
    checks: dict
    decision: str
    notes: str
    ai_disclosure_approved: bool

    def __post_init__(self):
        for value in (self.shop_id, self.job_id, self.output_asset_id, self.reviewer_user_id):
            canonical_uuid(value)
        if self.source_asset_id is not None:
            canonical_uuid(self.source_asset_id)
        if type(self.reviewed_sha256) is not str or len(self.reviewed_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.reviewed_sha256
        ):
            raise MotionError("Missing immutable clip hash for visual review")
        if self.decision not in ("APPROVED", "REJECTED"):
            raise MotionError("Human quality decision required")
        if type(self.checks) not in (dict, MappingProxyType) or set(self.checks) != set(CATEGORIES):
            raise MotionError("Incomplete visual acceptance checklist")
        if any(type(v) is not bool for v in self.checks.values()):
            raise MotionError("Each visual check must be manually assessed")
        if type(self.notes) is not str or len(self.notes.strip()) < 12 or len(self.notes) > 1000:
            raise MotionError("Reviewer explanation required")
        if type(self.ai_disclosure_approved) is not bool:
            raise MotionError("Disclosure review required")
        # frozen=True does NOT freeze a caller-provided dict. Deep-copy the
        # primitive bool checklist into an immutable mapping, so a caller
        # cannot flip any human approval after constructing the receipt.
        object.__setattr__(self,"checks",MappingProxyType(dict(self.checks)))

    def approved_for_feature4(self, *, authoritative_shop_id: str, actual_media_sha256: str,
                              reviewer_has_write_role: bool) -> bool:
        canonical_uuid(authoritative_shop_id)
        if authoritative_shop_id != self.shop_id or reviewer_has_write_role is not True:
            raise MotionError("Reviewer is not authorized for this tenant")
        if actual_media_sha256 != self.reviewed_sha256:
            raise MotionError("Clip changed after the visual review")
        if (self.decision != "APPROVED" or not all(self.checks.values()) or
            self.ai_disclosure_approved is not True):
            raise MotionError("Visual quality or AI disclosure not approved")
        return True


def review_template() -> dict:
    """Fail-closed checklist; pending reviewer must fill every criterion."""
    return {name: False for name in CATEGORIES}
