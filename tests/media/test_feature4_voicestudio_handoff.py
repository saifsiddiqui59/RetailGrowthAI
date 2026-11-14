"""Feature4 VoiceStudio original-audio to real compiler contract, offline only."""
import copy
import io
from hashlib import sha256
from pathlib import Path
import sys
import unittest
from uuid import uuid4
import wave

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_voicestudio_handoff import compile_voicestudio_narrated_reel
from creative_contract import CreativeContractError
from test_feature4_intent_compiler import pair


def pcm(seconds=30):
    out=io.BytesIO()
    with wave.open(out,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
        w.writeframes(b"\x02\x01" * (8000*seconds))
    return out.getvalue()


class VoiceStudioHandoffTests(unittest.TestCase):
    def setup_case(self):
        draft, snapshot=pair()
        asset_id=str(uuid4()); request_id=str(uuid4())
        snapshot["assets"][asset_id] = {
            **copy.deepcopy(snapshot["assets"]["musicowned"]),
            "object_path": f"{snapshot['shop_id']}/voicestudio/{snapshot['campaign_id']}/{request_id}/render.wav",
            "mime_type": "audio/wav",
        }
        draft["voiceover_asset_id"]=asset_id
        data=pcm()
        receipt={"shop_id":snapshot["shop_id"],"campaign_id":snapshot["campaign_id"],
                 "audio_asset_id":asset_id,"request_id":request_id,
                 "review_status":"APPROVED_FOR_EDITING","private":True,
                 "rights_reviewed":True,"revoked_at":None,
                 "render_duration_seconds":30,
                 "feature4_audio_sha256":sha256(data).hexdigest()}
        return draft,snapshot,receipt,data

    def call(self,draft,snapshot,receipt,data,*,reader=None):
        return compile_voicestudio_narrated_reel(
            draft=draft,snapshot=snapshot,
            read_current_receipt=reader or (lambda *args:dict(receipt)),
            read_current_private_wav=lambda *args:data,
        )

    def test_real_feature4_compiler_receives_only_approved_private_audio(self):
        draft,snapshot,receipt,data=self.setup_case()
        result=self.call(draft,snapshot,receipt,data)
        aid=draft["voiceover_asset_id"]
        self.assertEqual(result["request"]["voiceover_asset_id"],aid)
        self.assertEqual(result["request"]["voiceover_source"],"retailer")
        self.assertEqual(result["manifest"]["assets"][aid]["shop_id"],snapshot["shop_id"])
        self.assertEqual(result["bundle"]["assets"][aid]["object_path"],
                         snapshot["assets"][aid]["object_path"])
        exported = result["bundle"]["assets"][aid]
        for key in ("shop_id", "object_path", "storage_bucket", "mime_type",
                    "license_name", "rights_source", "rights_evidence",
                    "source_feature", "kind", "approved"):
            self.assertEqual(exported[key], snapshot["assets"][aid][key])
        worker = result["manifest"]["assets"][aid]
        self.assertEqual(worker["shop_id"], snapshot["shop_id"])
        self.assertEqual(worker["kind"], "audio")
        self.assertEqual(worker["source_feature"], "retailer")
        self.assertTrue(worker["approved"])
        self.assertTrue(worker["path"])
        self.assertEqual(worker["rights"], {
            "license": exported["license_name"], "commercial_use": True,
            "source": exported["rights_source"],
            "evidence": exported["rights_evidence"],
        })
        self.assertNotIn("voiceover_source",draft)

    def test_malformed_trusted_brand_denied_before_private_read(self):
        # A corrupt trusted snapshot must never escape as AttributeError or
        # access private WAV/receipt bytes before its shape is validated.
        for malformed in (None, [], "brand", False):
            draft, snapshot, receipt, data = self.setup_case()
            snapshot["brand"] = malformed
            reads = []
            with self.subTest(brand=malformed), self.assertRaisesRegex(
                    CreativeContractError, "Trusted narration brand required"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=lambda *_: reads.append("receipt") or dict(receipt),
                    read_current_private_wav=lambda *_: reads.append("wav") or data)
            self.assertEqual(reads, [])

    def test_other_reviewed_media_denied_before_private_wav_read(self):
        # The narration approval cannot authorize reading a private WAV when
        # the accompanying music/footage has been removed or revoked.
        for defect in ("missing", "foreign", "revoked"):
            draft, snapshot, receipt, data = self.setup_case()
            music_id = draft["music_asset_id"]
            if defect == "missing":
                del snapshot["assets"][music_id]
            elif defect == "foreign":
                snapshot["assets"][music_id]["shop_id"] = str(uuid4())
            else:
                snapshot["assets"][music_id]["approved"] = False
            receipt_reads, wav_reads = [], []
            with self.subTest(defect=defect), self.assertRaisesRegex(
                    CreativeContractError, "Reviewed media missing, foreign or revoked"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=lambda *_: receipt_reads.append(True) or dict(receipt),
                    read_current_private_wav=lambda *_: wav_reads.append(True) or data)
            self.assertEqual(receipt_reads, [])
            self.assertEqual(wav_reads, [])

    def test_unlicensed_companion_denied_before_private_read(self):
        for field, invalid in (("license_name", "unknown"),
                               ("rights_source", " "),
                               ("rights_evidence", None)):
            draft, snapshot, receipt, data = self.setup_case()
            music = snapshot["assets"][draft["music_asset_id"]]
            music[field] = invalid
            reads = []
            with self.subTest(field=field), self.assertRaisesRegex(
                    CreativeContractError, "companion media rights missing"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=lambda *_: reads.append("receipt") or dict(receipt),
                    read_current_private_wav=lambda *_: reads.append("wav") or data)
            self.assertEqual(reads, [])

    def test_private_object_alias_rejected_before_wav_reader(self):
        # A second media ID may not reuse the approved VoiceStudio object,
        # even when the unrelated media row claims separate rights.
        draft, snapshot, receipt, data = self.setup_case()
        narration = snapshot["assets"][draft["voiceover_asset_id"]]
        other_id = next(key for key in snapshot["assets"]
                        if key != draft["voiceover_asset_id"])
        snapshot["assets"][other_id]["storage_bucket"] = narration["storage_bucket"]
        snapshot["assets"][other_id]["object_path"] = narration["object_path"]
        reads = []
        with self.assertRaisesRegex(CreativeContractError, "object aliases another media asset"):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: dict(receipt),
                read_current_private_wav=lambda *_: reads.append(True) or data)
        self.assertEqual(reads, [], "Aliased private WAV must not be fetched")

    def test_private_voice_cannot_be_reused_as_scene_footage_before_read(self):
        # The narration receipt grants audio mixing, never image/video use.
        draft, snapshot, receipt, data = self.setup_case()
        draft["scenes"][0]["asset_id"] = draft["voiceover_asset_id"]
        receipt_reads, wav_reads = [], []
        with self.assertRaisesRegex(CreativeContractError, "music, SFX or footage"):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: receipt_reads.append(True) or dict(receipt),
                read_current_private_wav=lambda *_: wav_reads.append(True) or data,
            )
        self.assertEqual(receipt_reads, [])
        self.assertEqual(wav_reads, [])

    def test_private_voice_cannot_be_reused_as_overlay_or_logo_before_read(self):
        # A voice-only approval never authorizes image overlays or brand logos.
        for placement in ("overlay", "logo"):
            draft, snapshot, receipt, data = self.setup_case()
            voice_id = draft["voiceover_asset_id"]
            if placement == "overlay":
                draft["scenes"][0]["poster_overlay_asset_id"] = voice_id
            else:
                snapshot.setdefault("brand", {})["logo_asset_id"] = voice_id
            reads = []
            with self.subTest(placement=placement), self.assertRaisesRegex(
                    CreativeContractError, "reused as"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=lambda *_: reads.append("receipt") or dict(receipt),
                    read_current_private_wav=lambda *_: reads.append("wav") or data)
            self.assertEqual(reads, [])

    def test_compiler_cannot_rewrite_other_worker_media_rights(self):
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original_compiler = adapter.compile_approved_storyboard
        for field, forged in (
            ("shop_id", str(uuid4())),
            ("kind", "video"),
            ("source_feature", "unreviewed"),
            ("approved", False),
            ("rights", {"license": "unreviewed", "commercial_use": False}),
        ):
            draft, snapshot, receipt, data = self.setup_case()
            music_id = draft["music_asset_id"]
            def altered_compiler(*args):
                output = original_compiler(*args)
                output["manifest"]["assets"][music_id][field] = forged
                return output
            with self.subTest(field=field), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=altered_compiler):
                with self.assertRaisesRegex(
                        CreativeContractError, "reviewed worker media rights"):
                    self.call(draft, snapshot, receipt, data)

    def test_revoked_other_media_during_compilation_fails_closed(self):
        # A soundtrack can be revoked after its initial validation but while
        # the existing compiler is building the worker manifest.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        music_id = draft["music_asset_id"]

        def concurrent_revocation(*args):
            result = original(*args)
            snapshot["assets"][music_id]["approved"] = False
            return result

        with patch.object(adapter, "compile_approved_storyboard",
                          side_effect=concurrent_revocation):
            with self.assertRaisesRegex(
                    CreativeContractError, "reviewed media changed during compilation"):
                self.call(draft, snapshot, receipt, data)

    def test_modified_pcm_never_reaches_compiler_even_with_valid_wav_header(self):
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        draft, snapshot, receipt, data = self.setup_case()
        altered = bytearray(data)
        altered[-2] ^= 1  # Valid PCM profile, but no longer approved bytes.
        with patch.object(adapter, "compile_approved_storyboard") as compiler:
            with self.assertRaisesRegex(CreativeContractError, "private narration bytes changed"):
                self.call(draft, snapshot, receipt, bytes(altered))
            compiler.assert_not_called()

    def test_compiler_cannot_inject_unsafe_worker_audio_path(self):
        # Even trusted compiler output is a boundary before FFmpeg opens files.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original_compiler = adapter.compile_approved_storyboard
        for unsafe in ("../private.wav", "/etc/passwd", "assets/../../secret.wav",
                       "C:\\private.wav", "C:private.wav", "-i", "-filter_complex", "https://evil.test/voice.wav",
                       "assets/%2e%2e/voice.wav", "assets//voice.wav", "assets/./voice.wav",
                       "assets/voice\\n.wav", "assets/voice\u202e.wav",
                       "assets/voice\u200b.wav", "assets/vоice.wav", "assets/voicé.wav",
                       "assets/voice\u00a0.wav", "in99.mp3", "in99.pcm"):
            draft, snapshot, receipt, data = self.setup_case()
            def forged_compiler(*args):
                output = original_compiler(*args)
                output["manifest"]["assets"][draft["voiceover_asset_id"]]["path"] = unsafe
                return output
            with self.subTest(path=unsafe), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged_compiler):
                with self.assertRaisesRegex(CreativeContractError, "manifest changed"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_windows_device_narration_worker_paths(self):
        # The worker may stage on Windows or a case-insensitive mounted volume.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for unsafe in ("assets/CON.wav", "assets/nul.wav", "assets/COM1.wav",
                       "assets/LPT9.wav", "assets/voice./render.wav"):
            draft, snapshot, receipt, data = self.setup_case()
            def forged(*args):
                result = original(*args)
                result["manifest"]["assets"][draft["voiceover_asset_id"]]["path"] = unsafe
                return result
            with self.subTest(path=unsafe), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(CreativeContractError, "manifest changed"):
                    self.call(draft, snapshot, receipt, data)

    def test_private_object_equivalent_alias_rejected_before_wav_read(self):
        for transform in (
            lambda key: key.replace("/", chr(92)),
            lambda key: key.replace("/render.wav", "/./render.wav"),
            lambda key: key.replace("/render.wav", "/temp/../render.wav"),
            lambda key: key + ".",
        ):
            draft, snapshot, receipt, data = self.setup_case()
            voice_id = draft["voiceover_asset_id"]
            other_id = draft["music_asset_id"]
            snapshot["assets"][other_id]["storage_bucket"] = "retailgrowth-media"
            snapshot["assets"][other_id]["object_path"] = transform(
                snapshot["assets"][voice_id]["object_path"])
            reads = []
            with self.subTest(transform=transform), self.assertRaisesRegex(
                    CreativeContractError, "object aliases another media asset"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=lambda *_: reads.append("receipt") or dict(receipt),
                    read_current_private_wav=lambda *_: reads.append("wav") or data)
            self.assertNotIn("wav", reads)

    def test_compiler_cannot_alias_private_voice_object_as_other_media(self):
        # Distinct asset IDs and staging filenames must not share one private
        # VoiceStudio object key, even when the worker paths differ.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        aid = draft["voiceover_asset_id"]

        def forged(*args):
            output = original(*args)
            other_id = next(key for key in output["bundle"]["assets"] if key != aid)
            output["bundle"]["assets"][other_id]["storage_bucket"] = (
                output["bundle"]["assets"][aid]["storage_bucket"]
            )
            output["bundle"]["assets"][other_id]["object_path"] = (
                output["bundle"]["assets"][aid]["object_path"]
            )
            return output

        with patch.object(adapter, "compile_approved_storyboard", side_effect=forged):
            with self.assertRaisesRegex(CreativeContractError, "object aliases another asset"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_equivalent_private_object_aliases(self):
        # A compromised compiler must not reintroduce a differently spelled
        # private WAV key after the trusted snapshot passed pre-read checks.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for alias in ("backslash", "dot", "parent", "trailing-dot", "uppercase"):
            draft, snapshot, receipt, data = self.setup_case()
            voice_id = draft["voiceover_asset_id"]

            def forged(*args):
                output = original(*args)
                other_id = next(key for key in output["bundle"]["assets"]
                                if key != voice_id)
                voice = output["bundle"]["assets"][voice_id]
                key = voice["object_path"]
                variants = {
                    "backslash": key.replace("/", chr(92)),
                    "dot": key.replace("/render.wav", "/./render.wav"),
                    "parent": key.replace("/render.wav", "/temp/../render.wav"),
                    "trailing-dot": key + ".",
                    "uppercase": key.upper(),
                }
                output["bundle"]["assets"][other_id]["storage_bucket"] = voice["storage_bucket"]
                output["bundle"]["assets"][other_id]["object_path"] = variants[alias]
                return output

            with self.subTest(alias=alias), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(
                        CreativeContractError, "object aliases another asset"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_relicense_other_reviewed_media(self):
        # A trusted voice receipt must not permit a compiler to rewrite the
        # selected music/footage tenant, storage origin or license evidence.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for field, replacement in (
            ("shop_id", str(uuid4())),
            ("object_path", "foreign/unauthorized.mp3"),
            ("storage_bucket", "public"),
            ("license_name", "unreviewed"),
            ("rights_evidence", "forged approval"),
        ):
            draft, snapshot, receipt, data = self.setup_case()
            music_id = draft["music_asset_id"]

            def forged(*args):
                output = original(*args)
                output["bundle"]["assets"][music_id][field] = replacement
                return output

            with self.subTest(field=field), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(
                        CreativeContractError, "reviewed asset rights or origin"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_swap_reviewed_poster_overlay(self):
        # Existing approved IDs are not interchangeable: the editor reviewed
        # the exact overlay on this scene, not any other licensed media.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        scene = draft["scenes"][0]
        original_overlay = scene.get("poster_overlay_asset_id")
        other_id = next(key for key in snapshot["assets"]
                        if key not in (draft["voiceover_asset_id"], original_overlay))
        # Keep the approved draft valid; mutate only the compiler output.
        # Changing the draft itself is rejected earlier by the normal
        # distinct-Feature3-poster contract and never exercises this guard.

        def forged(*args):
            result = original(*args)
            result["request"]["scenes"][0]["poster_overlay_asset_id"] = other_id
            return result

        with patch.object(adapter, "compile_approved_storyboard", side_effect=forged):
            with self.assertRaisesRegex(
                    CreativeContractError, "changed reviewed media selection"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_drop_reviewed_media_from_both_worker_maps(self):
        # A subset-only asset check misses omissions when both maps agree.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for kind in ("music", "scene"):
            draft, snapshot, receipt, data = self.setup_case()
            target = (draft["music_asset_id"] if kind == "music"
                      else draft["scenes"][0]["asset_id"])
            self.assertIsNotNone(target)

            def forged(*args):
                output = original(*args)
                output["bundle"]["assets"].pop(target)
                output["manifest"]["assets"].pop(target)
                return output

            with self.subTest(kind=kind), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(CreativeContractError, "omitted reviewed media"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_inject_unreviewed_media_ids(self):
        # Reject a new asset ID injected after the trusted media snapshot was
        # approved, whether inserted into the bundle or the FFmpeg manifest.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for target in ("bundle", "manifest"):
            draft, snapshot, receipt, data = self.setup_case()
            def forged(*args):
                result = original(*args)
                result[target]["assets"][str(uuid4())] = {
                    "shop_id": snapshot["shop_id"], "approved": True,
                    "kind": "audio", "path": "assets/injected.wav",
                }
                return result
            with self.subTest(target=target), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(CreativeContractError, "unapproved media asset"):
                    self.call(draft, snapshot, receipt, data)


    def test_compiler_rejects_unsafe_non_voice_worker_paths(self):
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for unsafe in ("../foreign.mp3", "/etc/passwd", "assets/../foreign.mp3",
                       "https://evil.test/a.mp3", "assets/CON.mp3",
                       "assets/foreign.mp3.", "assets/foreign\\\\clip.mp3"):
            draft, snapshot, receipt, data = self.setup_case()
            voice_id = draft["voiceover_asset_id"]

            def forged(*args):
                output = original(*args)
                other_id = next(key for key in output["manifest"]["assets"]
                                if key != voice_id)
                output["manifest"]["assets"][other_id]["path"] = unsafe
                return output

            with self.subTest(path=unsafe), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(
                        CreativeContractError, "Unsafe compiled reviewed media worker path"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_collision_between_non_voice_worker_assets(self):
        # Two independently reviewed assets must never overwrite one another
        # in the FFmpeg staging directory, even if narration itself is safe.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        voice_id = draft["voiceover_asset_id"]

        def aliased(*args):
            output = original(*args)
            others = [key for key in output["manifest"]["assets"] if key != voice_id]
            assert len(others) >= 2
            source_path = output["manifest"]["assets"][others[0]]["path"]
            output["manifest"]["assets"][others[1]]["path"] = source_path
            return output

        with patch.object(adapter, "compile_approved_storyboard", side_effect=aliased):
            with self.assertRaisesRegex(CreativeContractError, "reviewed media worker paths alias"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_alias_private_voice_worker_path_with_other_media(self):
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        aid = draft["voiceover_asset_id"]

        def aliased(*args):
            result = original(*args)
            other_id = next(key for key in result["manifest"]["assets"] if key != aid)
            result["manifest"]["assets"][aid]["path"] = result["manifest"]["assets"][other_id]["path"]
            return result

        with patch.object(adapter, "compile_approved_storyboard", side_effect=aliased):
            with self.assertRaisesRegex(CreativeContractError, "manifest changed|aliases another asset"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_normalized_worker_path_collision(self):
        # A distinct textual path may still resolve to the same staged WAV.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        aid = draft["voiceover_asset_id"]

        def aliased(*args):
            result = original(*args)
            other_id = next(key for key in result["manifest"]["assets"] if key != aid)
            narration = result["manifest"]["assets"][aid]["path"]
            result["manifest"]["assets"][other_id]["path"] = "temp/../" + narration
            return result

        with patch.object(adapter, "compile_approved_storyboard", side_effect=aliased):
            with self.assertRaisesRegex(CreativeContractError, "aliases another asset"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_casefolded_worker_path_collision(self):
        # Case-insensitive staging filesystems must not overwrite approved audio.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        aid = draft["voiceover_asset_id"]

        def aliased(*args):
            result = original(*args)
            other_id = next(key for key in result["manifest"]["assets"] if key != aid)
            narration = result["manifest"]["assets"][aid]["path"]
            # The other asset can use an otherwise distinct path string that
            # aliases narration on Windows or case-insensitive mounted media.
            result["manifest"]["assets"][other_id]["path"] = narration.upper()
            return result

        with patch.object(adapter, "compile_approved_storyboard", side_effect=aliased):
            with self.assertRaisesRegex(CreativeContractError, "aliases another asset"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_windows_trimmed_staging_aliases(self):
        # Windows strips trailing dots/spaces from filename components and
        # treats backslashes as separators; neither may alias approved WAV.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for transform in (
            lambda path: path + ".",
            lambda path: path.replace("/", "\\\\"),
            lambda path: path.replace("/", "/./"),
        ):
            draft, snapshot, receipt, data = self.setup_case()
            aid = draft["voiceover_asset_id"]

            def forged(*args):
                output = original(*args)
                other_id = next(key for key in output["manifest"]["assets"] if key != aid)
                output["manifest"]["assets"][other_id]["path"] = transform(
                    output["manifest"]["assets"][aid]["path"]
                )
                return output

            with self.subTest(transform=transform), patch.object(
                adapter, "compile_approved_storyboard", side_effect=forged
            ):
                with self.assertRaisesRegex(CreativeContractError, "aliases another asset"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_rejects_unicode_compatibility_staging_alias(self):
        # Fullwidth ASCII normalizes to the same worker filename on systems
        # that apply Unicode compatibility normalization before opening it.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        draft, snapshot, receipt, data = self.setup_case()
        aid = draft["voiceover_asset_id"]

        def forged(*args):
            output = original(*args)
            other_id = next(key for key in output["manifest"]["assets"] if key != aid)
            narration = output["manifest"]["assets"][aid]["path"]
            output["manifest"]["assets"][other_id]["path"] = "".join(
                chr(ord(ch) + 0xFEE0) if "!" <= ch <= "~" else ch
                for ch in narration
            )
            return output

        with patch.object(adapter, "compile_approved_storyboard", side_effect=forged):
            with self.assertRaisesRegex(CreativeContractError, "aliases another asset"):
                self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_retarget_approved_narration_scope(self):
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original_compiler = adapter.compile_approved_storyboard
        for key, forged in (("shop_id", str(uuid4())),
                            ("duration_seconds", 15),
                            ("campaign_id", str(uuid4()))):
            draft, snapshot, receipt, data = self.setup_case()
            def forged_compiler(*args):
                result = original_compiler(*args)
                result["request"][key] = forged
                return result
            with self.subTest(key=key), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged_compiler):
                with self.assertRaisesRegex(CreativeContractError, "request scope changed"):
                    self.call(draft, snapshot, receipt, data)

    def test_malformed_compiler_output_denied_with_contract_error(self):
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        for malformed in (None, [], "not a reel", {}, {"request": []},
                          {"request": {}, "bundle": None, "manifest": {}},
                          {"request": {}, "bundle": {"assets": []}, "manifest": {"assets": {}}},
                          {"request": {}, "bundle": {"assets": {}}, "manifest": {"assets": None}}):
            draft, snapshot, receipt, data = self.setup_case()
            with self.subTest(malformed=malformed), patch.object(
                    adapter, "compile_approved_storyboard", return_value=malformed):
                with self.assertRaisesRegex(CreativeContractError, "Malformed compiled"):
                    self.call(draft, snapshot, receipt, data)

    def test_private_narration_cannot_be_reused_as_soundtrack_or_sfx(self):
        # Approval is purpose-scoped: voiceover is not a music/SFX license.
        for reuse in ("music", "sfx"):
            draft, snapshot, receipt, data = self.setup_case()
            aid = draft["voiceover_asset_id"]
            if reuse == "music":
                draft["music_asset_id"] = aid
            else:
                draft["scenes"][0]["sfx_asset_id"] = aid
            reads = []
            with self.subTest(reuse=reuse), self.assertRaisesRegex(
                    CreativeContractError, "cannot be reused"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=lambda *_: reads.append("receipt") or dict(receipt),
                    read_current_private_wav=lambda *_: reads.append("wav") or data)
            self.assertEqual(reads, [], "Invalid audio purpose must fail before private I/O")

    def test_compiler_cannot_substitute_other_approved_music_or_footage(self):
        # A different approved asset in the snapshot is not automatically
        # approved for this reviewed edit, even with valid tenant rights.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for field in ("music", "footage", "sfx"):
            draft, snapshot, receipt, data = self.setup_case()
            def forged(*args):
                result = original(*args)
                if field == "music":
                    result["request"]["music_asset_id"] = str(uuid4())
                elif field == "footage":
                    result["request"]["scenes"][0]["asset_id"] = str(uuid4())
                else:
                    result["request"]["scenes"][0]["sfx_asset_id"] = str(uuid4())
                return result
            with self.subTest(field=field), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(CreativeContractError, "reviewed media selection"):
                    self.call(draft, snapshot, receipt, data)

    def test_compiler_cannot_reuse_approved_voice_as_music_or_sfx(self):
        # Input purpose checks alone cannot constrain future compiler output.
        from unittest.mock import patch
        import feature4_voicestudio_handoff as adapter
        original = adapter.compile_approved_storyboard
        for reuse in ("music", "sfx"):
            draft, snapshot, receipt, data = self.setup_case()
            aid = draft["voiceover_asset_id"]

            def forged(*args):
                result = original(*args)
                if reuse == "music":
                    result["request"]["music_asset_id"] = aid
                else:
                    result["request"].setdefault("scenes", [{}])[0]["sfx_asset_id"] = aid
                return result

            with self.subTest(reuse=reuse), patch.object(
                    adapter, "compile_approved_storyboard", side_effect=forged):
                with self.assertRaisesRegex(CreativeContractError, "cannot be reused"):
                    self.call(draft, snapshot, receipt, data)

    def test_foreign_and_unapproved_sources_rejected(self):
        mutations=[
            lambda d,s,r: d.update(shop_id=str(uuid4())),
            lambda d,s,r: r.update(shop_id=str(uuid4())),
            lambda d,s,r: r.update(review_status="NEEDS_REVIEW"),
            lambda d,s,r: r.update(rights_reviewed=False),
            lambda d,s,r: r.update(revoked_at="2026-11-11T00:00:00Z"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(shop_id=str(uuid4())),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(approved=False),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(storage_bucket="public"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(object_path="foreign/render.wav"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(license_name="unknown"),
            lambda d,s,r: s["assets"][d["voiceover_asset_id"]].update(mime_type="audio/mpeg"),
        ]
        for mutate in mutations:
            draft,snapshot,receipt,data=self.setup_case()
            mutate(draft,snapshot,receipt)
            with self.subTest(mutate=mutate),self.assertRaises(CreativeContractError):
                self.call(draft,snapshot,receipt,data)

    def test_spoofed_voice_provider_or_campaign_denied_before_private_io(self):
        for key, forged in (("voiceover_source", "ai"),
                            ("voiceover_source", "voicestudio-unreviewed"),
                            ("campaign_id", str(uuid4()))):
            draft, snapshot, receipt, data = self.setup_case()
            draft[key] = forged
            calls = []
            def receipt_reader(*args):
                calls.append(args)
                return dict(receipt)
            with self.subTest(key=key, forged=forged), self.assertRaises(CreativeContractError):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=receipt_reader,
                    read_current_private_wav=lambda *_: data)
            self.assertEqual(calls, [], "Invalid scope must not access private media")

    def test_private_narration_rights_metadata_requires_nonblank_strings(self):
        # Truthy numbers, containers and whitespace are not legal evidence.
        for key in ("rights_source", "rights_evidence"):
            for forged in (True, 1, ["unreviewed"], {"claimed": True}, "   ", ""):
                draft, snapshot, receipt, data = self.setup_case()
                snapshot["assets"][draft["voiceover_asset_id"]][key] = forged
                with self.subTest(key=key, forged=forged), self.assertRaises(CreativeContractError):
                    self.call(draft, snapshot, receipt, data)

    def test_malformed_trusted_media_manifest_fails_closed(self):
        for invalid in (None, [], "not-a-manifest", 7):
            d,s,r,data=self.setup_case()
            s["assets"]=invalid
            with self.subTest(invalid=invalid), self.assertRaises(CreativeContractError):
                self.call(d,s,r,data)

    def test_trusted_receipt_type_confusion_denied(self):
        # Python considers True == 1, but durable approval must be boolean.
        for key, forged in (
            ("private", 1), ("rights_reviewed", 1),
            ("render_duration_seconds", 30.0),
            ("revoked_at", False),
        ):
            draft, snapshot, receipt, data = self.setup_case()
            receipt[key] = forged
            with self.subTest(key=key), self.assertRaises(CreativeContractError):
                self.call(draft, snapshot, receipt, data)

    def test_approved_high_rate_stereo_pcm_not_rejected_by_arbitrary_8mb_cap(self):
        # 30s at 96kHz stereo 16-bit is 11.52 MB, a valid bounded
        # narration profile under the existing supported sample-rate contract.
        d, s, r, _ = self.setup_case()
        out = io.BytesIO()
        with wave.open(out, "wb") as writer:
            writer.setnchannels(2)
            writer.setsampwidth(2)
            writer.setframerate(96000)
            writer.writeframes(bytes((2, 1, 4, 3)) * (96000 * 30))
        data = out.getvalue()
        self.assertGreater(len(data), 8 * 1024 * 1024)
        r["feature4_audio_sha256"] = sha256(data).hexdigest()
        result = self.call(d, s, r, data)
        self.assertEqual(result["request"]["voiceover_asset_id"], d["voiceover_asset_id"])

    def test_approved_60_second_stereo_narration_compiles(self):
        # Real PCM framing, not a forged RIFF size: cover the maximum
        # supported reel duration and stereo audio without paid synthesis.
        draft, snapshot, receipt, _ = self.setup_case()
        draft["duration_seconds"] = 60
        for index, scene in enumerate(draft["scenes"]):
            scene["start"] = index * 20
            scene["duration"] = 20
        receipt["render_duration_seconds"] = 60
        out = io.BytesIO()
        with wave.open(out, "wb") as writer:
            writer.setnchannels(2)
            writer.setsampwidth(2)
            writer.setframerate(48000)
            writer.writeframes(bytes((1, 2, 3, 4)) * (48000 * 60))
        data = out.getvalue()
        receipt["feature4_audio_sha256"] = sha256(data).hexdigest()
        result = self.call(draft, snapshot, receipt, data)
        self.assertEqual(result["request"]["voiceover_asset_id"], draft["voiceover_asset_id"])
        self.assertEqual(result["request"]["duration_seconds"], 60)

    def test_approved_15_second_narration_compiles_without_30_second_assumption(self):
        draft, snapshot, receipt, _ = self.setup_case()
        draft["duration_seconds"] = 15
        # The approved storyboard must also cover exactly 15s; changing only
        # the narration receipt leaves the original 30s scene timeline invalid.
        for index, scene in enumerate(draft["scenes"]):
            scene["start"] = index * 5
            scene["duration"] = 5
        receipt["render_duration_seconds"] = 15
        data = pcm(15)
        receipt["feature4_audio_sha256"] = sha256(data).hexdigest()
        result = self.call(draft, snapshot, receipt, data)
        self.assertEqual(result["request"]["voiceover_asset_id"], draft["voiceover_asset_id"])
        self.assertEqual(result["request"]["voiceover_source"], "retailer")

    def test_receipt_reader_cannot_mutate_scope_before_private_wav_access(self):
        # Receipt lookup is trusted I/O and may execute arbitrary callbacks.
        # It must not be allowed to change approved inputs before WAV access.
        for target in ("draft", "snapshot"):
            draft, snapshot, receipt, data = self.setup_case()
            private_reads = []
            def receipt_reader(*_):
                if target == "draft":
                    draft["duration_seconds"] = 15
                else:
                    snapshot["campaign_id"] = str(uuid4())
                return dict(receipt)
            with self.subTest(target=target), self.assertRaisesRegex(
                    CreativeContractError, "scope changed during receipt lookup"):
                compile_voicestudio_narrated_reel(
                    draft=draft, snapshot=snapshot,
                    read_current_receipt=receipt_reader,
                    read_current_private_wav=lambda *_: private_reads.append(True) or data)
            self.assertEqual(private_reads, [])

    def test_private_reader_cannot_mutate_approved_draft_timeline(self):
        draft, snapshot, receipt, data = self.setup_case()
        def changing_reader(*_):
            draft["duration_seconds"] = 15
            return data
        with self.assertRaisesRegex(CreativeContractError, "draft changed"):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: dict(receipt),
                read_current_private_wav=changing_reader)

    def test_private_reader_cannot_mutate_approved_draft_source(self):
        draft, snapshot, receipt, data = self.setup_case()
        def changing_reader(*_):
            draft["voiceover_source"] = "ai"
            return data
        with self.assertRaisesRegex(CreativeContractError, "draft changed"):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: dict(receipt),
                read_current_private_wav=changing_reader)

    def test_receipt_callback_cannot_swap_other_scene_before_private_wav_access(self):
        # A receipt lookup is trusted external I/O; reject a changed media
        # manifest before requesting any private narration bytes.
        draft, snapshot, receipt, data = self.setup_case()
        other = next(key for key in snapshot["assets"]
                     if key != draft["voiceover_asset_id"])
        private_reads = []
        def receipt_reader(*_):
            snapshot["assets"][other]["object_path"] = "foreign/changed-scene.mp4"
            return dict(receipt)
        with self.assertRaisesRegex(CreativeContractError,
                                    "scope changed during receipt lookup"):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=receipt_reader,
                read_current_private_wav=lambda *_: private_reads.append(True) or data)
        self.assertEqual(private_reads, [])

    def test_private_reader_cannot_swap_other_approved_scene_media(self):
        draft, snapshot, receipt, data = self.setup_case()
        other = next(key for key in snapshot["assets"] if key != draft["voiceover_asset_id"])
        def changing_reader(*_):
            snapshot["assets"][other]["object_path"] = "foreign/changed-scene.mp4"
            return data
        with self.assertRaisesRegex(CreativeContractError, "snapshot changed"):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: dict(receipt),
                read_current_private_wav=changing_reader)

    def test_private_reader_cannot_change_approved_campaign_scene_order(self):
        draft, snapshot, receipt, data = self.setup_case()
        def changing_reader(*_):
            snapshot["campaign_id"] = str(uuid4())
            return data
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: dict(receipt),
                read_current_private_wav=changing_reader)

    def test_wrong_receipt_duration_denied_before_private_media_read(self):
        draft, snapshot, receipt, data = self.setup_case()
        receipt["render_duration_seconds"] = 15
        private_reads = []
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=draft, snapshot=snapshot,
                read_current_receipt=lambda *_: dict(receipt),
                read_current_private_wav=lambda *_: private_reads.append(True) or data)
        self.assertEqual(private_reads, [])

    def test_non_bytes_private_media_rejected_before_compilation(self):
        for forged in (bytearray(pcm()), memoryview(pcm()), None, "not WAV"):
            draft, snapshot, receipt, _ = self.setup_case()
            with self.subTest(type=type(forged).__name__), self.assertRaises(CreativeContractError):
                self.call(draft, snapshot, receipt, forged)

    def test_bytes_changed_or_timeline_wrong_denied(self):
        d,s,r,data=self.setup_case()
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data[:-10])
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,pcm(15))

    def test_private_wav_rejects_trailing_bytes_and_forged_riff_size(self):
        # The digest can match a malformed private object; container framing
        # must independently reject bytes that wave.open silently ignores.
        for mutate in (
            lambda raw: raw + b"untrusted trailing bytes",
            lambda raw: raw[:4] + (len(raw) - 9).to_bytes(4, "little") + raw[8:],
            lambda raw: b"RIFX" + raw[4:],
        ):
            d,s,r,data=self.setup_case()
            malformed=mutate(data)
            r["feature4_audio_sha256"]=sha256(malformed).hexdigest()
            with self.subTest(mutate=mutate), self.assertRaises(CreativeContractError):
                self.call(d,s,r,malformed)

    def test_private_wav_rejects_hidden_riff_chunks(self):
        # A correct outer RIFF length is insufficient: wave.open ignores
        # unknown chunks after data, duplicate data and trailing bytes.
        for extra in (b"JUNK" + (4).to_bytes(4, "little") + b"evil",
                      b"data" + (2).to_bytes(4, "little") + b"xx",
                      b"JUNK" + (5).to_bytes(4, "little") + b"short"):
            d, s, r, data = self.setup_case()
            forged = data + extra
            forged = forged[:4] + (len(forged) - 8).to_bytes(4, "little") + forged[8:]
            r["feature4_audio_sha256"] = sha256(forged).hexdigest()
            with self.subTest(extra=extra), self.assertRaises(CreativeContractError):
                self.call(d, s, r, forged)

    def test_private_wav_rejects_empty_data_and_nonzero_padding(self):
        # Even a receipt whose digest matches cannot authorize ambiguous PCM.
        d, s, r, data = self.setup_case()
        empty = data[:40] + (0).to_bytes(4, "little")
        empty = empty[:4] + (len(empty) - 8).to_bytes(4, "little") + empty[8:]
        r["feature4_audio_sha256"] = sha256(empty).hexdigest()
        with self.assertRaises(CreativeContractError):
            self.call(d, s, r, empty)

        # A nonzero odd-chunk padding byte is not a canonical WAV object.
        d, s, r, data = self.setup_case()
        # Append an odd data payload and its deliberately nonzero pad byte.
        odd = data[:40] + (len(data) - 44 + 1).to_bytes(4, "little") + data[44:] + b"\x01\xff"
        odd = odd[:4] + (len(odd) - 8).to_bytes(4, "little") + odd[8:]
        r["feature4_audio_sha256"] = sha256(odd).hexdigest()
        with self.assertRaises(CreativeContractError):
            self.call(d, s, r, odd)

    def test_private_wav_rejects_inconsistent_pcm_headers_and_partial_frames(self):
        # Valid SHA and RIFF length do not make a forged PCM layout safe.
        for offset, width, value in (
            (22, 2, 3),        # unsupported three-channel PCM
            (32, 2, 1),        # block alignment disagrees with channels
            (28, 4, 1),        # byte rate disagrees with sample rate
            (24, 4, 0),        # invalid sample rate
            (34, 2, 24),       # unsupported 24-bit PCM
        ):
            d, s, r, data = self.setup_case()
            forged = data[:offset] + value.to_bytes(width, "little") + data[offset + width:]
            r["feature4_audio_sha256"] = sha256(forged).hexdigest()
            with self.subTest(offset=offset, value=value), self.assertRaises(CreativeContractError):
                self.call(d, s, r, forged)

        d, s, r, data = self.setup_case()
        # Add one unaligned PCM byte and a legal zero RIFF padding byte.
        payload = data[:40] + (len(data) - 44 + 1).to_bytes(4, "little") + data[44:] + bytes((1, 0))
        payload = payload[:4] + (len(payload) - 8).to_bytes(4, "little") + payload[8:]
        r["feature4_audio_sha256"] = sha256(payload).hexdigest()
        with self.assertRaises(CreativeContractError):
            self.call(d, s, r, payload)

    def test_private_wav_rejects_duplicate_format_and_unknown_predata_chunks(self):
        # A valid matching SHA must not make extra RIFF metadata trusted.
        # Neither an additional fmt chunk nor an unreviewed JUNK chunk is
        # part of the canonical private PCM handoff accepted by Feature4.
        for extra in (
            b"fmt " + (16).to_bytes(4, "little") + pcm() [20:36],
            b"JUNK" + (4).to_bytes(4, "little") + b"test",
        ):
            d, s, r, data = self.setup_case()
            forged = data[:36] + extra + data[36:]
            forged = forged[:4] + (len(forged) - 8).to_bytes(4, "little") + forged[8:]
            r["feature4_audio_sha256"] = sha256(forged).hexdigest()
            with self.subTest(chunk=extra[:4]), self.assertRaises(CreativeContractError):
                self.call(d, s, r, forged)

    def test_private_wav_rejects_out_of_range_sample_rate_with_matching_digest(self):
        for rate in (7999, 96001):
            d, s, r, data = self.setup_case()
            forged = bytearray(data)
            forged[24:28] = rate.to_bytes(4, "little")
            forged[28:32] = (rate * 2).to_bytes(4, "little")
            raw = bytes(forged)
            r["feature4_audio_sha256"] = sha256(raw).hexdigest()
            with self.subTest(rate=rate), self.assertRaises(CreativeContractError):
                self.call(d, s, r, raw)

    def test_revocation_during_read_is_not_accepted(self):
        d,s,r,data=self.setup_case()
        counts=[0]
        def reader(*_):
            counts[0]+=1
            answer=dict(r)
            if counts[0]>1:answer["revoked_at"]="revoked"
            return answer
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(counts[0],2)

    def test_revocation_after_compilation_is_not_accepted(self):
        d,s,r,data=self.setup_case()
        counts=[0]
        def reader(*_):
            counts[0]+=1
            answer=dict(r)
            if counts[0]>=3:
                answer["review_status"]="REVOKED"
            return answer
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(counts[0],3)

    def test_in_place_receipt_revocation_during_read_denied(self):
        # A trusted service reader can return the same mutable cached dict.
        # An aliased baseline must never hide a post-read approval change.
        d,s,r,data=self.setup_case()
        calls=[0]
        def reader(*_):
            calls[0]+=1
            if calls[0]==2:
                r["review_status"]="REVOKED"
            return r
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(calls[0],2)

    def test_in_place_receipt_revocation_during_compile_denied(self):
        d,s,r,data=self.setup_case()
        calls=[0]
        def reader(*_):
            calls[0]+=1
            if calls[0]==3:
                r["revoked_at"]="2026-11-11T00:00:00Z"
            return r
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(calls[0],3)

    def test_private_media_replacement_during_read_denied(self):
        d,s,r,data=self.setup_case()
        asset=d["voiceover_asset_id"]
        def private_reader(*_):
            s["assets"][asset]["object_path"]="other-tenant/forged.wav"
            return data
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,
                read_current_receipt=lambda *_:dict(r),
                read_current_private_wav=private_reader)

    def test_private_media_replacement_during_compile_denied(self):
        d,s,r,data=self.setup_case()
        asset=d["voiceover_asset_id"]
        reads=[0]
        def receipt_reader(*_):
            reads[0]+=1
            if reads[0]==3:
                s["assets"][asset]["rights_evidence"]="replaced-during-compile"
            return dict(r)
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,
                read_current_receipt=receipt_reader,
                read_current_private_wav=lambda *_:data)
        self.assertEqual(reads[0],3)

    def test_private_bytes_replaced_during_compilation_denied(self):
        d,s,r,data=self.setup_case()
        calls=[0]
        def private_reader(*_):
            calls[0]+=1
            return data if calls[0]==1 else data[:-2]+b"\x00\x00"
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,
                read_current_receipt=lambda *_:dict(r),
                read_current_private_wav=private_reader)
        self.assertEqual(calls[0],2)

    def test_revocation_after_final_private_read_denied(self):
        d,s,r,data=self.setup_case()
        calls=[0]
        def reader(*_):
            calls[0]+=1
            answer=dict(r)
            if calls[0]>=4:answer["review_status"]="REVOKED"
            return answer
        with self.assertRaises(CreativeContractError):
            self.call(d,s,r,data,reader=reader)
        self.assertEqual(calls[0],4)

    def test_no_browser_supplied_audio_reader_or_receipt(self):
        d,s,r,data=self.setup_case()
        with self.assertRaises(CreativeContractError):
            compile_voicestudio_narrated_reel(
                draft=d,snapshot=s,read_current_receipt=r,read_current_private_wav=data)

if __name__=="__main__":
    unittest.main()
