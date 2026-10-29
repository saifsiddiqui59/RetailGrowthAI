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
            if ident in {v["id"] for v in catalog()}:
                if ident in found or (row.get("Locale") not in ("en-IN","hi-IN","mr-IN") or
                                      row.get("Gender") not in ("Male","Female") or
                                      row.get("VoiceType") not in ("Neural","Standard","NeuralHD")):
                    raise VoiceCatalogUnavailable("Provider voice identity differs")
                found[ident]=row
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
