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
    # Never reinterpret a browser-selected provider or an unrelated campaign
    # as an approved retailer-owned VoiceStudio narration source.
    if draft.get("voiceover_source") not in (None, "retailer"):
        raise CreativeContractError("VoiceStudio narration source must be retailer-approved")
    if "campaign_id" in draft and draft["campaign_id"] != campaign:
        raise CreativeContractError("VoiceStudio narration campaign mismatch")
    # An approved narration receipt authorizes voiceover only. Reusing the same
    # private WAV as background music or scene SFX would silently broaden its
    # reviewed purpose and may double-mix the voice into the final Reel.
    scenes = draft.get("scenes")
    if draft.get("music_asset_id") == asset_id or (
        type(scenes) is list and any(
            type(scene) is dict and scene.get("sfx_asset_id") == asset_id
            for scene in scenes
        )
    ):
        raise CreativeContractError("Approved narration cannot be reused as music or SFX")
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
                or type(row.get("rights_source")) is not str
                or not row["rights_source"].strip()
                or type(row.get("rights_evidence")) is not str
                or not row["rights_evidence"].strip()):
            raise CreativeContractError("Feature4 trusted media does not match private VoiceStudio asset")
        return record

    # Freeze the request before invoking external trusted readers: a callback
    # must not change duration, source or selected media between approval and
    # the final compilation (the receipt is bound to the original duration).
    frozen_draft = deepcopy(draft)
    # Other approved scene/music/media inputs must remain immutable while
    # trusted callbacks run; checking only the narration row is insufficient.
    frozen_snapshot = deepcopy(snapshot)
    # Freeze the trusted receipt: a service reader may reuse and mutate its dict.
    # Comparing against a live alias would silently accept in-place revocation.
    before = deepcopy(authoritative())
    # A receipt callback is external trusted I/O too: deny mutations before
    # accessing the private WAV, not only after its bytes have been read.
    if draft != frozen_draft or snapshot != frozen_snapshot:
        raise CreativeContractError("Narration scope changed during receipt lookup")
    # Freeze trusted media metadata as well as approval: a private reader or
    # compiler must not silently replace the tenant object while processing.
    before_asset = deepcopy(snapshot["assets"][asset_id])
    original = read_current_private_wav(shop, campaign, asset_id)
    if (type(original) is not bytes or not 44 <= len(original)
            <= 44 + duration * 96000 * 2 * 2):
        raise CreativeContractError("Bounded private narration bytes required")
    # wave.open accepts trailing bytes and ignores an inconsistent RIFF length.
    # A private asset must be one complete, canonical RIFF/WAVE object.
    if (original[:4] != b"RIFF" or original[8:12] != b"WAVE"
            or int.from_bytes(original[4:8], "little") != len(original) - 8):
        raise CreativeContractError("Private narration RIFF length or type invalid")
    # Validate the complete RIFF chunk walk, not just its outer length.
    # wave.open can ignore bytes after the PCM data chunk, even when the
    # forged RIFF length includes them. Reject ambiguous trailing payloads.
    offset = 12
    seen_fmt = seen_data = False
    while offset < len(original):
        if offset + 8 > len(original):
            raise CreativeContractError("Truncated private narration WAV chunk")
        kind = original[offset:offset + 4]
        size = int.from_bytes(original[offset + 4:offset + 8], "little")
        end = offset + 8 + size
        padded_end = end + (size & 1)
        if padded_end > len(original):
            raise CreativeContractError("Private narration WAV chunk exceeds RIFF")
        if size & 1 and original[end] != 0:
            raise CreativeContractError("Nonzero private narration WAV padding")
        if kind == b"data" and size == 0:
            raise CreativeContractError("Empty private narration PCM data")
        if kind == b"fmt ":
            if seen_fmt or seen_data or size != 16 or int.from_bytes(original[offset + 8:offset + 10], "little") != 1:
                raise CreativeContractError("Noncanonical private narration PCM format")
            channels = int.from_bytes(original[offset + 10:offset + 12], "little")
            sample_rate = int.from_bytes(original[offset + 12:offset + 16], "little")
            byte_rate = int.from_bytes(original[offset + 16:offset + 20], "little")
            block_align = int.from_bytes(original[offset + 20:offset + 22], "little")
            bits = int.from_bytes(original[offset + 22:offset + 24], "little")
            if (channels not in (1, 2) or not 8000 <= sample_rate <= 96000
                    or bits != 16 or block_align != channels * 2
                    or byte_rate != sample_rate * block_align):
                raise CreativeContractError("Inconsistent private narration PCM format")
            seen_fmt = True
        elif kind == b"data":
            if not seen_fmt or seen_data or padded_end != len(original):
                raise CreativeContractError("Private narration WAV data is not terminal")
            if size != duration * sample_rate * block_align:
                raise CreativeContractError("Private narration PCM data length mismatch")
            seen_data = True
        else:
            raise CreativeContractError("Unexpected private narration WAV chunk")
        offset = padded_end
    if not seen_fmt or not seen_data:
        raise CreativeContractError("Private narration WAV chunks missing")
    if sha256(original).hexdigest() != before["feature4_audio_sha256"]:
        raise CreativeContractError("VoiceStudio private narration bytes changed")
    try:
        with wave.open(io.BytesIO(original), "rb") as reader:
            frames, rate = reader.getnframes(), reader.getframerate()
            if (reader.getnchannels() not in (1, 2) or reader.getsampwidth() != 2
                    or rate < 8000 or rate > 96000 or reader.getcomptype() != "NONE"
                    or frames != duration * rate
                    or reader.getnframes() * reader.getnchannels() * 2 != size):
                raise CreativeContractError("Narration timeline/profile does not match approved reel")
    except (EOFError, wave.Error) as exc:
        raise CreativeContractError("Malformed private narration WAV") from exc
    if authoritative() != before or snapshot["assets"].get(asset_id) != before_asset:
        raise CreativeContractError("Narration approval or private asset changed during read")
    if draft != frozen_draft:
        raise CreativeContractError("Narration draft changed during private read")
    if snapshot != frozen_snapshot:
        raise CreativeContractError("Approved reel snapshot changed during private read")
    output = compile_approved_storyboard(deepcopy(frozen_draft), deepcopy(snapshot))
    if output["request"].get("voiceover_asset_id") != asset_id or output["request"].get("voiceover_source") != "retailer":
        raise CreativeContractError("Video compiler discarded approved voice source")
    # The worker manifest intentionally replaces private object keys with
    # sandbox-local paths; verify its rights and identity separately from
    # the authoritative bundle, which must preserve the private object key.
    bundle_asset = output.get("bundle", {}).get("assets", {}).get(asset_id)
    if type(bundle_asset) is not dict or any(
        bundle_asset.get(key) != before_asset.get(key)
        for key in ("shop_id", "object_path", "storage_bucket", "mime_type",
                    "license_name", "rights_source", "rights_evidence",
                    "source_feature", "kind", "approved")
    ):
        raise CreativeContractError("Compiled private narration bundle changed")
    manifest_asset = output.get("manifest", {}).get("assets", {}).get(asset_id)
    if (type(manifest_asset) is not dict
            or manifest_asset.get("shop_id") != shop
            or manifest_asset.get("kind") != "audio"
            or manifest_asset.get("source_feature") != "retailer"
            or manifest_asset.get("approved") is not True
            or type(manifest_asset.get("path")) is not str
            or not manifest_asset["path"].strip()
            or manifest_asset.get("rights") != {
                "license": before_asset["license_name"],
                "commercial_use": True,
                "source": before_asset["rights_source"],
                "evidence": before_asset["rights_evidence"],
            }):
        raise CreativeContractError("Compiled private narration manifest changed")
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
    if (draft != frozen_draft or snapshot != frozen_snapshot or authoritative() != before
            or snapshot["assets"].get(asset_id) != before_asset):
        raise CreativeContractError("Narration changed after final private read")
    return output
