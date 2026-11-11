"""Feature4 consumes the existing VoiceStudio private WAV *only after review*.

Pure server-side adapter to existing compile_approved_storyboard contract. Does
not modify the video renderer, call the VoiceStudio model, authorize a user,
write Supabase rows or grant publishing permission. The request and trusted
private readers must originate from current signed tenant/RLS service context.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import io
import re
from uuid import UUID
import wave

from creative_contract import CreativeContractError
from feature4_intent_compiler import compile_approved_storyboard

_HASH = re.compile(r"^[0-9a-f]{64}$")


def _uuid4(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (ValueError, TypeError, AttributeError):
        return False


def compile_voicestudio_narrated_reel(*, draft, snapshot,
                                     read_current_receipt, read_current_private_wav):
    """Create an F4 compilation using already-approved same-shop WAV.

    Both readers are trusted authenticated service functions; the client cannot
    supply a source path, receipt, voice content, rights or review state. The
    current receipt is rechecked after reading bounded original private bytes.
    """
    if (type(draft) is not dict or type(snapshot) is not dict
            or not callable(read_current_receipt)
            or not callable(read_current_private_wav)
            or draft.get("voiceover_asset_id") is None):
        raise CreativeContractError("Current approved private VoiceStudio source required")
    shop, campaign, asset_id = snapshot.get("shop_id"), snapshot.get("campaign_id"), draft["voiceover_asset_id"]
    if not (_uuid4(shop) and _uuid4(campaign) and _uuid4(asset_id)):
        raise CreativeContractError("Canonical private narration scope required")
    if draft.get("shop_id") != shop:
        raise CreativeContractError("Voice request tenant mismatch")
    duration = draft.get("duration_seconds")
    if type(duration) is not int or duration not in (15, 30, 60):
        raise CreativeContractError("Invalid approved narration timeline")

    def authoritative():
        record = read_current_receipt(shop, campaign, asset_id)
        if type(record) is not dict or any(type(record.get(k)) is not type(v) or record.get(k) != v for k, v in (
            ("shop_id", shop), ("campaign_id", campaign),
            ("audio_asset_id", asset_id),
            ("review_status", "APPROVED_FOR_EDITING"),
            ("private", True), ("rights_reviewed", True),
            ("revoked_at", None), ("render_duration_seconds", duration),
        )):
            raise CreativeContractError("Private VoiceStudio source unapproved or revoked")
        digest = record.get("feature4_audio_sha256")
        request_id = record.get("request_id")
        if type(digest) is not str or not _HASH.fullmatch(digest) or not _uuid4(request_id):
            raise CreativeContractError("Missing private narration origin digest")
        assets = snapshot.get("assets")
        if type(assets) is not dict:
            raise CreativeContractError("Trusted private media manifest required")
        row = assets.get(asset_id)
        expected_path = f"{shop}/voicestudio/{campaign}/{request_id}/render.wav"
        if (type(row) is not dict or row.get("shop_id") != shop
                or row.get("approved") is not True
                or row.get("kind") != "audio"
                or row.get("source_feature") != "retailer"
                or row.get("storage_bucket") != "retailgrowth-media"
                or row.get("object_path") != expected_path
                or row.get("mime_type") != "audio/wav"
                or row.get("license_name") not in ("owned", "commercial")
                or not row.get("rights_source") or not row.get("rights_evidence")):
            raise CreativeContractError("Feature4 trusted media does not match private VoiceStudio asset")
        return record

    # Freeze the trusted receipt: a service reader may reuse and mutate its dict.
    # Comparing against a live alias would silently accept in-place revocation.
    before = deepcopy(authoritative())
    # Freeze trusted media metadata as well as approval: a private reader or
    # compiler must not silently replace the tenant object while processing.
    before_asset = deepcopy(snapshot["assets"][asset_id])
    original = read_current_private_wav(shop, campaign, asset_id)
    if type(original) is not bytes or not 44 <= len(original) <= 8 * 1024 * 1024:
        raise CreativeContractError("Bounded private narration bytes required")
    # wave.open accepts trailing bytes and ignores an inconsistent RIFF length.
    # A private asset must be one complete, canonical RIFF/WAVE object.
    if (original[:4] != b"RIFF" or original[8:12] != b"WAVE"
            or int.from_bytes(original[4:8], "little") != len(original) - 8):
        raise CreativeContractError("Private narration RIFF length or type invalid")
    if sha256(original).hexdigest() != before["feature4_audio_sha256"]:
        raise CreativeContractError("VoiceStudio private narration bytes changed")
    try:
        with wave.open(io.BytesIO(original), "rb") as reader:
            frames, rate = reader.getnframes(), reader.getframerate()
            if (reader.getnchannels() not in (1, 2) or reader.getsampwidth() != 2
                    or rate < 8000 or rate > 96000 or reader.getcomptype() != "NONE"
                    or frames != duration * rate
                    or len(reader.readframes(frames)) != frames * reader.getnchannels() * 2):
                raise CreativeContractError("Narration timeline/profile does not match approved reel")
    except (EOFError, wave.Error) as exc:
        raise CreativeContractError("Malformed private narration WAV") from exc
    if authoritative() != before or snapshot["assets"].get(asset_id) != before_asset:
        raise CreativeContractError("Narration approval or private asset changed during read")
    output = compile_approved_storyboard(deepcopy(draft), deepcopy(snapshot))
    if output["request"].get("voiceover_asset_id") != asset_id or output["request"].get("voiceover_source") != "retailer":
        raise CreativeContractError("Video compiler discarded approved voice source")
    # The compiler may perform additional trusted reads. Do not return a reel
    # compiled from narration whose approval was revoked during that work.
    if authoritative() != before or snapshot["assets"].get(asset_id) != before_asset:
        raise CreativeContractError("Narration approval or private asset changed during compilation")
    # Re-read the authoritative private object after compilation. A mutable
    # storage key could be replaced without changing its approval receipt.
    final_bytes = read_current_private_wav(shop, campaign, asset_id)
    if (type(final_bytes) is not bytes or len(final_bytes) != len(original)
            or sha256(final_bytes).hexdigest() != before["feature4_audio_sha256"]):
        raise CreativeContractError("Private narration replaced during compilation")
    if authoritative() != before or snapshot["assets"].get(asset_id) != before_asset:
        raise CreativeContractError("Narration changed after final private read")
    return output
