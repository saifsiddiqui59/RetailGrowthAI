"""Region-specific Azure neural voices/list preflight, no TTS synthesis.

Only exposes safe public selection metadata to signed app; caller injects the
authoritative actor/shop reader. Never returns Azure key, billing or JWT.
Default OFF, no network under ordinary CI. No browser-provided endpoints.
"""
from __future__ import annotations
import json
import os
import re
from urllib.request import Request, build_opener
from .feature2_azure_speech import catalog, _NoRedirect

_REGION = re.compile(r"^[a-z0-9]{2,30}$")
_MAX_JSON = 256 * 1024

class VoiceCatalogUnavailable(ValueError):
    pass

def _fetch_region_voices(url, headers):
    req = Request(url, headers=headers, method="GET")
    with build_opener(_NoRedirect()).open(req, timeout=12) as response:
        if response.geturl() != url or response.status != 200 or (
            "application/json" not in response.headers.get("Content-Type", "").lower()):
            raise VoiceCatalogUnavailable("Speech catalog origin/format not verified")
        payload = response.read(_MAX_JSON + 1)
    if len(payload) > _MAX_JSON:
        raise VoiceCatalogUnavailable("Speech voice catalog oversized")
    return json.loads(payload.decode("utf-8"))

def published_voices_in_region(*, region, api_key, shop_id, actor_may_read_shop,
                               transport=None):
    if os.environ.get("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED") != "true":
        raise VoiceCatalogUnavailable("Speech selection is disabled")
    if (not isinstance(region, str) or not _REGION.fullmatch(region) or
        not isinstance(api_key, str) or len(api_key) < 12 or
        not callable(actor_may_read_shop) or
        actor_may_read_shop(shop_id) is not True):
        raise VoiceCatalogUnavailable("Authorized region/tenant speech setup required")
    url="https://" + region + ".tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers={"Ocp-Apim-Subscription-Key":api_key,
             "User-Agent":"RetailGrowthAI-Feature2-VoiceCatalog/1.0"}
    try:
        response=(transport or _fetch_region_voices)(url,headers)
        if type(response) is not list or len(response)>1000:
            raise VoiceCatalogUnavailable("Untrusted Azure voice catalog")
        found={}
        for row in response:
            if type(row) is not dict:
                raise VoiceCatalogUnavailable("Malformed voice catalog entry")
            ident=row.get("ShortName")
            curated = next((v for v in catalog() if v["id"] == ident), None)
            if curated is not None:
                if (ident in found or row.get("Locale") != curated["locale"] or
                    row.get("Gender") != curated["gender"] or
                    row.get("VoiceType") not in ("Neural", "Standard", "NeuralHD")):
                    raise VoiceCatalogUnavailable("Provider voice identity differs")
                found[ident] = row
        if actor_may_read_shop(shop_id) is not True:
            raise VoiceCatalogUnavailable("Shop read permission changed")
        result=[{**v,"region_verified":True} for v in catalog()
                if v["id"] in found and
                v["locale"]==found[v["id"]]["Locale"] and
                v["gender"]==found[v["id"]]["Gender"]]
        # Never mark unavailable voices selectable: no silent fallback/upgrade.
        return {"schema":"retailgrowth.feature2-speech-voices.v1",
                "region":region,"available_voices":result,
                "configured_voice_candidates":len(catalog()),
                "resource_catalog_queried":True,
                "tts_call_made":False,
                "published":False}
    except VoiceCatalogUnavailable:
        raise
    except Exception as exc:
        raise VoiceCatalogUnavailable("Real regional voice availability unverified") from exc


# Route *selection* only. This never supplies an authenticated model call,
# immutable voice inventory, invoice approval, external API URL or audio bytes.
# Kokoro v1.0 is US/GB English, not English-India/Hindi/Marathi.
from .feature2_kokoro_local import SUPPORTED_VOICES


def route_voice_selection(*, shop_id, campaign_id, locale, voice_id,
                          current_editor, user_confirmed_charge=False,
                          read_verified_region_voices=None):
    """Review-only explicit language/provider split, without silent fallback.

    Region selection is trusted only through the server callback returning an
    already-validated speech catalog snapshot for this same shop/campaign.
    Caller must still reserve usage, verify billing, and stage original WAV.
    """
    from uuid import UUID
    def uid(s):
        try:
            return type(s) is str and str(UUID(s))==s and UUID(s).version==4
        except (ValueError, TypeError, AttributeError):
            return False
    if (not uid(shop_id) or not uid(campaign_id) or
        not callable(current_editor) or
        current_editor(shop_id,campaign_id) is not True or
        type(locale) is not str or type(voice_id) is not str or
        type(user_confirmed_charge) is not bool):
        raise VoiceCatalogUnavailable("Authenticated voice request required")
    local=SUPPORTED_VOICES.get(voice_id)
    if local is not None:
        if locale!=local:
            raise VoiceCatalogUnavailable("Kokoro voice has different locale")
        output={"provider":"kokoro-onnx","voice_id":voice_id,"locale":locale,
                "region_verified":False,"paid_tts":False,
                "requires_explicit_charge":False}
    else:
        selected=next((row for row in catalog() if row["id"]==voice_id),None)
        if (selected is None or locale!=selected["locale"] or
            locale not in ("en-IN","hi-IN","mr-IN") or
            user_confirmed_charge is not True or
            not callable(read_verified_region_voices)):
            raise VoiceCatalogUnavailable(
                "Indian language needs opted-in verified paid-region voice")
        checked=read_verified_region_voices(shop_id,campaign_id)
        if (type(checked) is not dict or
            checked.get("schema")!="retailgrowth.feature2-speech-voices.v1" or
            checked.get("resource_catalog_queried") is not True or
            type(checked.get("available_voices")) is not list or
            not any(type(row) is dict and row.get("id")==voice_id and
                    row.get("locale")==locale and
                    row.get("region_verified") is True
                    for row in checked["available_voices"])):
            raise VoiceCatalogUnavailable("Voice not validated in configured region")
        output={"provider":"azure-speech-opt-in","voice_id":voice_id,
                "locale":locale,"region_verified":True,
                "paid_tts":True,"requires_explicit_charge":True}
    if current_editor(shop_id,campaign_id) is not True:
        raise VoiceCatalogUnavailable("Editor revoked during voice route selection")
    return {
        "schema":"retailgrowth.feature2-voice-provider-review.v1",
        "shop_id":shop_id,"campaign_id":campaign_id,**output,
        "route_status":"SOURCE_ONLY_EDITOR_REVIEW",
        "model_call_made":False,"cost_reserved":False,
        "can_dispatch":False,"can_publish":False,
        "no_automatic_azure_fallback":True,
    }
