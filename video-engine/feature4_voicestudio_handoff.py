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
import posixpath
import re
import unicodedata
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
            type(scene) is dict and (scene.get("sfx_asset_id") == asset_id or scene.get("asset_id") == asset_id or scene.get("poster_overlay_asset_id") == asset_id)
            for scene in scenes
        )
    ):
        raise CreativeContractError("Approved narration cannot be reused as music, SFX or footage")
    if snapshot.get("brand", {}).get("logo_asset_id") == asset_id:
        raise CreativeContractError("Approved narration cannot be reused as brand logo")
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
        # Reject private-object aliasing in the trusted snapshot before any
        # private WAV bytes are fetched. The compiled-output check below is a
        # second fence, not a substitute for this pre-I/O tenant/media gate.
        for other_id, other in assets.items():
            if other_id == asset_id:
                continue
            if (type(other) is dict
                    and other.get("storage_bucket") == row["storage_bucket"]
                    and other.get("object_path") == row["object_path"]):
                raise CreativeContractError("Private narration object aliases another media asset")
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
    # Never hand unverified private bytes to the compiler: the receipt digest
    # binds the exact approved PCM object, not merely its WAV header/profile.
    if sha256(original).hexdigest() != before["feature4_audio_sha256"]:
        raise CreativeContractError("Private narration digest differs from approved receipt")
    if authoritative() != before or snapshot["assets"].get(asset_id) != before_asset:
        raise CreativeContractError("Narration approval or private asset changed during read")
    if draft != frozen_draft:
        raise CreativeContractError("Narration draft changed during private read")
    if snapshot != frozen_snapshot:
        raise CreativeContractError("Approved reel snapshot changed during private read")
    output = compile_approved_storyboard(deepcopy(frozen_draft), deepcopy(snapshot))
    # A compromised or incompatible compiler must fail with a contract error,
    # never an AttributeError after reading private tenant narration.
    if (type(output) is not dict or type(output.get("request")) is not dict
            or type(output.get("bundle")) is not dict
            or type(output["bundle"].get("assets")) is not dict
            or type(output.get("manifest")) is not dict
            or type(output["manifest"].get("assets")) is not dict):
        raise CreativeContractError("Malformed compiled private narration output")
    # The compiler must not silently retarget an approved voice to another
    # tenant, campaign or timeline after the private source has been verified.
    request = output["request"]
    if (request.get("shop_id") != shop
            or request.get("duration_seconds") != duration
            or ("campaign_id" in request and request["campaign_id"] != campaign)):
        raise CreativeContractError("Compiled narration request scope changed")
    if request.get("voiceover_asset_id") != asset_id or request.get("voiceover_source") != "retailer":
        raise CreativeContractError("Video compiler discarded approved voice source")
    # Purpose misuse takes precedence over generic media-selection parity.
    # This preserves a distinct fail-closed worker audit for narration reuse.
    compiled_scenes = request.get("scenes")
    if request.get("music_asset_id") == asset_id or (
        type(compiled_scenes) is list and any(
            type(scene) is dict and
            (scene.get("sfx_asset_id") == asset_id or scene.get("asset_id") == asset_id or scene.get("poster_overlay_asset_id") == asset_id)
            for scene in compiled_scenes
        )
    ):
        raise CreativeContractError("Compiled narration cannot be reused as music, SFX or footage")
    if output.get("bundle", {}).get("brand", {}).get("logo_asset_id") == asset_id or request.get("logo_asset_id") == asset_id:
        raise CreativeContractError("Compiled narration cannot be reused as brand logo")
    # A compiler must not substitute a different already-trusted media ID:
    # approval of a private narration does not authorize changing the music
    # or footage selected by the reviewed storyboard.
    source_scenes = frozen_draft.get("scenes")
    rendered_scenes = request.get("scenes")
    if (request.get("music_asset_id") != frozen_draft.get("music_asset_id")
            or type(source_scenes) is not list
            or type(rendered_scenes) is not list
            or len(source_scenes) != len(rendered_scenes)
            or any(type(before_scene) is not dict or type(after_scene) is not dict
                   or before_scene.get("asset_id") != after_scene.get("asset_id")
                   or before_scene.get("sfx_asset_id") != after_scene.get("sfx_asset_id")
                   for before_scene, after_scene in zip(source_scenes, rendered_scenes))):
        raise CreativeContractError("Compiled narration changed reviewed media selection")
    # Recheck purpose at the compiled boundary: a future compiler revision must
    # not reintroduce approved voice as background music or scene effects.
    compiled_scenes = request.get("scenes")
    if request.get("music_asset_id") == asset_id or (
        type(compiled_scenes) is list and any(
            type(scene) is dict and (scene.get("sfx_asset_id") == asset_id or scene.get("asset_id") == asset_id or scene.get("poster_overlay_asset_id") == asset_id)
            for scene in compiled_scenes
        )
    ):
        raise CreativeContractError("Compiled narration cannot be reused as music, SFX or footage")
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
    # The approved private object is purpose-scoped to narration. A second
    # asset ID must never point at the same private bucket/key: downstream
    # staging could fetch the approved WAV as unreviewed music or footage.
    # This also catches forged compiler bundle entries not present in the
    # original trusted snapshot.
    for other_id, other in output["bundle"]["assets"].items():
        if other_id == asset_id or type(other) is not dict:
            continue
        if (other.get("storage_bucket") == before_asset["storage_bucket"]
                and other.get("object_path") == before_asset["object_path"]):
            raise CreativeContractError("Compiled private narration object aliases another asset")
    # Only assets selected from the trusted snapshot may enter the worker.
    # A compromised compiler cannot append an unreviewed media row under a
    # fresh ID, even if the private narration row itself is unchanged.
    trusted_ids = set(snapshot["assets"])
    if (set(output["bundle"]["assets"]) - trusted_ids
            or set(output["manifest"]["assets"]) - trusted_ids
            or set(output["bundle"]["assets"]) != set(output["manifest"]["assets"])):
        raise CreativeContractError("Compiled narration introduced unapproved media asset")
    # The narration receipt cannot authorize rewriting the rights or private
    # origin of OTHER reviewed media. The compiler may stage local paths in
    # its worker manifest, but the immutable bundle must retain each trusted
    # source row's tenant, object identity and license evidence.
    for selected_id, compiled_row in output["bundle"]["assets"].items():
        trusted_row = frozen_snapshot["assets"].get(selected_id)
        if (type(compiled_row) is not dict or type(trusted_row) is not dict
                or any(compiled_row.get(field) != trusted_row.get(field)
                       for field in ("shop_id", "storage_bucket", "object_path",
                                     "mime_type", "kind", "source_feature",
                                     "approved", "license_name", "rights_source",
                                     "rights_evidence"))):
            raise CreativeContractError("Compiled narration changed reviewed asset rights or origin")
    # Every selected reviewed asset must survive the compiler-to-worker handoff.
    # The subset check above prevents injection but cannot detect a compiler
    # silently dropping music, an overlay, or a scene asset from both maps.
    selected_ids = {asset_id}
    if frozen_draft.get("music_asset_id") is not None:
        selected_ids.add(frozen_draft["music_asset_id"])
    for scene in frozen_draft["scenes"]:
        for key in ("asset_id", "sfx_asset_id", "poster_overlay_asset_id"):
            if scene.get(key) is not None:
                selected_ids.add(scene[key])
    logo_id = frozen_snapshot.get("brand", {}).get("logo_asset_id")
    if logo_id is not None:
        selected_ids.add(logo_id)
    if (set(output["bundle"]["assets"]) != selected_ids
            or set(output["manifest"]["assets"]) != selected_ids):
        raise CreativeContractError("Compiled narration omitted reviewed media asset")
    manifest_asset = output.get("manifest", {}).get("assets", {}).get(asset_id)
    if (type(manifest_asset) is not dict
            or manifest_asset.get("shop_id") != shop
            or manifest_asset.get("kind") != "audio"
            or manifest_asset.get("source_feature") != "retailer"
            or manifest_asset.get("approved") is not True
            or type(manifest_asset.get("path")) is not str
            or not manifest_asset["path"].strip()
            # Worker paths must stay relative to its sandbox. Never pass an
            # absolute path, traversal, Windows separator or control byte to FFmpeg.
            or manifest_asset["path"].startswith(("/", "\\", "-"))
            or "\\" in manifest_asset["path"]
            # Reject drive-relative and URI-shaped paths as well as percent-encoded
            # traversal. Worker paths are literal sandbox paths, never URLs.
            or ":" in manifest_asset["path"]
            or "%" in manifest_asset["path"]
            or any(part in ("", ".", "..") for part in manifest_asset["path"].split("/"))
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in manifest_asset["path"])
            # Invisible formatting controls (e.g. bidi overrides) can disguise
            # the worker path in review logs even when its bytes are relative.
            or any(unicodedata.category(ch) == "Cf" for ch in manifest_asset["path"])
            # Restrict the server-created worker path to unambiguous ASCII.
            # Unicode lookalikes and nonprinting marks are not needed for IDs.
            or not re.fullmatch(r"[A-Za-z0-9_./-]+", manifest_asset["path"])
            # Windows device names and trailing-dot components can resolve
            # differently from the reviewed sandbox path on worker hosts.
            or any(
                part.rstrip(" .").upper().split(".")[0] in
                {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
                or part.endswith((" ", "."))
                for part in manifest_asset["path"].split("/")
            )
            # A verified PCM/WAV must not be handed to FFmpeg under a
            # different container extension by a compromised compiler.
            or not manifest_asset["path"].endswith(".wav")
            or manifest_asset.get("rights") != {
                "license": before_asset["license_name"],
                "commercial_use": True,
                "source": before_asset["rights_source"],
                "evidence": before_asset["rights_evidence"],
            }):
        raise CreativeContractError("Compiled private narration manifest changed")
    # A relative path can still alias another approved media asset. Never let
    # the narration share a staged worker filename with music, SFX or footage:
    # the worker could then mix or overwrite unrelated tenant-approved bytes.
    narration_path = manifest_asset["path"]
    # Preserve dot segments until posixpath.normpath collapses traversal.
    # rstrip(" .") on ".." would erase it, missing aliases such as
    # temp/../approved.wav on the worker filesystem.
    if any(
        other_id != asset_id and type(other) is dict
        and type(other.get("path")) is str
        and posixpath.normpath("/".join((part if part in (".", "..") else part.rstrip(" .")) for part in unicodedata.normalize("NFKC", other["path"]).replace("\\", "/").split("/"))).casefold() == narration_path.casefold()
        for other_id, other in output["manifest"]["assets"].items()
    ):
        raise CreativeContractError("Compiled private narration worker path aliases another asset")
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
