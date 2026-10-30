import pytest
from ai_agents.feature2_azure_speech import (
    published_voices_in_region, VoiceCatalogUnavailable, catalog,
)

SHOP="11111111-1111-4111-8111-111111111111"
def valid_row(name="hi-IN-SwaraNeural",locale="hi-IN",gender="Female"):
    return {"ShortName":name,"Locale":locale,"Gender":gender,"VoiceType":"Neural"}
def call(monkeypatch,data=None,actor=lambda shop:shop==SHOP):
    monkeypatch.setenv("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED","true")
    records=[]
    def transport(url,headers):
        records.append((url,headers))
        return data if data is not None else [valid_row()]
    def run():
        return published_voices_in_region(region="centralindia",api_key="fake-server-only-12345",
            shop_id=SHOP,actor_may_read_shop=actor,transport=transport)
    return run,records

def test_live_response_shape_narrows_only_to_actual_region_available(monkeypatch):
    run,calls=call(monkeypatch,[valid_row(),valid_row("en-IN-PrabhatNeural","en-IN","Male"),
                               valid_row("en-US-GuyNeural","en-US","Male")])
    r=run()
    assert len(r["available_voices"])==2
    assert {x["id"] for x in r["available_voices"]}=={"en-IN-PrabhatNeural","hi-IN-SwaraNeural"}
    assert all(x["region_verified"] for x in r["available_voices"])
    assert r["tts_call_made"] is False
    assert calls[0][0]=="https://centralindia.tts.speech.microsoft.com/cognitiveservices/voices/list"
    assert "Ocp-Apim-Subscription-Key" in calls[0][1]

@pytest.mark.parametrize("bad",[
    [valid_row(),valid_row()],
    [valid_row(gender="Male")],
    [valid_row(locale="en-IN")],
    [{"ShortName":"hi-IN-SwaraNeural","VoiceType":"unknown","Locale":"hi-IN","Gender":"Female"}],
    {"not":"list"},
])
def test_invalid_catalog_or_spoofed_provider_voice_fails_closed(monkeypatch,bad):
    run,_=call(monkeypatch,bad)
    with pytest.raises(VoiceCatalogUnavailable):run()

def test_disabled_or_revoked_shop_does_not_call_external_server(monkeypatch):
    run,calls=call(monkeypatch,actor=lambda _:False)
    with pytest.raises(VoiceCatalogUnavailable):run()
    assert not calls
    run,calls=call(monkeypatch)
    monkeypatch.delenv("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED")
    with pytest.raises(VoiceCatalogUnavailable):run()
    assert not calls

from ai_agents.feature2_azure_speech import route_voice_selection
CAMPAIGN="22222222-2222-4222-8222-222222222222"

def signed_region_fixture(*voices, region="centralindia"):
    # This deterministic regional shape is not a live signed Azure receipt.
    allowed={v["id"]:v for v in catalog()}
    return {"schema":"retailgrowth.feature2-speech-voices.v1",
            "region":region,"configured_voice_candidates":len(catalog()),
            "resource_catalog_queried":True,"tts_call_made":False,
            "published":False,
            "available_voices":[{**allowed[v],"region_verified":True}
                                for v in voices]}

@pytest.mark.parametrize("locale,voice",[
    ("en-us","af_heart"),("en-gb","bm_george"),
    ("en-IN","en-IN-NeerjaNeural"),("en-IN","en-IN-PrabhatNeural"),
    ("hi-IN","hi-IN-SwaraNeural"),("hi-IN","hi-IN-MadhurNeural"),
    ("mr-IN","mr-IN-AarohiNeural"),("mr-IN","mr-IN-ManoharNeural")
])
def test_provider_route_is_locale_specific_and_never_dispatches(locale,voice):
    def trusted_catalog(*a):
        return signed_region_fixture(voice)
    out=route_voice_selection(
        shop_id=SHOP,campaign_id=CAMPAIGN,
        locale=locale,voice_id=voice,
        current_editor=lambda *a:True,
        user_confirmed_charge=True,
        read_verified_region_voices=trusted_catalog)
    expected="kokoro-onnx" if locale in ("en-us","en-gb") else "azure-speech-opt-in"
    assert out["provider"]==expected
    assert out["paid_tts"]==(expected=="azure-speech-opt-in")
    assert out["model_call_made"] is False
    assert out["cost_reserved"] is False
    assert out["can_dispatch"] is False
    assert out["no_automatic_azure_fallback"] is True
    assert out["can_publish"] is False

@pytest.mark.parametrize("locale,voice",[
    ("hi-IN","af_heart"),("mr-IN","af_heart"),("en-IN","af_heart"),
    ("en-us","hi-IN-SwaraNeural"),("mr-IN","hi-IN-SwaraNeural"),
    ("en-gb","af_heart"),("en-US","af_heart"),
    ("mr-IN","unverified_mr_voice"),("xx-XX","af_heart")
])
def test_cross_locale_and_nonexistent_provider_is_denied_before_cost(locale,voice):
    calls=[]
    with pytest.raises(VoiceCatalogUnavailable):
        route_voice_selection(shop_id=SHOP,campaign_id=CAMPAIGN,
            locale=locale,voice_id=voice,
            current_editor=lambda *a:True,
            user_confirmed_charge=True,
            read_verified_region_voices=lambda *a:calls.append(a) or {})
    assert not calls or calls==[(SHOP,CAMPAIGN)]

def test_indian_voices_require_explicit_charge_and_verified_region_catalog():
    calls=[]
    def reader(*a):
        calls.append(a)
        return signed_region_fixture("hi-IN-SwaraNeural")
    with pytest.raises(VoiceCatalogUnavailable,match="opted-in"):
        route_voice_selection(shop_id=SHOP,campaign_id=CAMPAIGN,
            locale="hi-IN",voice_id="hi-IN-SwaraNeural",
            current_editor=lambda *a:True,read_verified_region_voices=reader)
    assert calls==[]
    with pytest.raises(VoiceCatalogUnavailable,match="region"):
        route_voice_selection(shop_id=SHOP,campaign_id=CAMPAIGN,
            locale="mr-IN",voice_id="mr-IN-AarohiNeural",
            user_confirmed_charge=True,current_editor=lambda *a:True,
            read_verified_region_voices=reader)

def test_voice_route_rechecks_editor_after_catalog_lookup():
    seen=[]
    def auth(*a):
        seen.append(1)
        return len(seen)==1
    with pytest.raises(VoiceCatalogUnavailable,match="revoked"):
        route_voice_selection(shop_id=SHOP,campaign_id=CAMPAIGN,
            locale="hi-IN",voice_id="hi-IN-SwaraNeural",
            user_confirmed_charge=True,current_editor=auth,
            read_verified_region_voices=lambda *a:
                signed_region_fixture("hi-IN-SwaraNeural"))
    assert len(seen)==2

def test_local_kokoro_does_not_need_azure_voice_catalog_or_charge():
    out=route_voice_selection(
        shop_id=SHOP,campaign_id=CAMPAIGN,voice_id="af_sarah",
        locale="en-us",current_editor=lambda *a:True,
        user_confirmed_charge=False,
        read_verified_region_voices=lambda *a:(_ for _ in ()).throw(
            AssertionError("Free Kokoro must not query Azure")))
    assert out["provider"]=="kokoro-onnx" and not out["paid_tts"]


def test_region_voice_catalog_does_not_accept_standard_as_neural(monkeypatch):
    # A published name alone must not approve an incompatible provider class.
    run,_=call(monkeypatch,[{**valid_row(),"VoiceType":"Standard"}])
    with pytest.raises(VoiceCatalogUnavailable,match="identity"):
        run()


def test_real_catalog_projection_to_route_uses_full_regional_shape(monkeypatch):
    run,_=call(monkeypatch,[valid_row(),valid_row(
        "en-IN-PrabhatNeural","en-IN","Male")])
    snapshot=run()  # injected source fixture; no live Azure or speech call.
    chosen=route_voice_selection(
        shop_id=SHOP,campaign_id=CAMPAIGN,locale="en-IN",
        voice_id="en-IN-PrabhatNeural",
        current_editor=lambda *scope:True,user_confirmed_charge=True,
        read_verified_region_voices=lambda *scope:snapshot)
    assert chosen["provider"]=="azure-speech-opt-in"
    assert chosen["region_verified"] is True
    assert chosen["model_call_made"] is False
    assert chosen["cost_reserved"] is False


@pytest.mark.parametrize("change",[
    {"region":"https://evil.com"},{"region":""},{"region":None},
    {"resource_catalog_queried":"true"},{"tts_call_made":True},
    {"published":True},{"configured_voice_candidates":1000},
    {"available_voices":[]},
    {"available_voices":[{"id":"hi-IN-SwaraNeural","region_verified":True}]},
])
def test_paid_voice_route_rejects_forged_or_incomplete_region_snapshot(change):
    original=signed_region_fixture("hi-IN-SwaraNeural")
    original.update(change)
    with pytest.raises(VoiceCatalogUnavailable,match="catalog|region"):
        route_voice_selection(
            shop_id=SHOP,campaign_id=CAMPAIGN,locale="hi-IN",
            voice_id="hi-IN-SwaraNeural",
            current_editor=lambda *scope:True,user_confirmed_charge=True,
            read_verified_region_voices=lambda *scope:original)


def test_paid_voice_route_denies_duplicate_or_cross_locale_catalog_records():
    same=signed_region_fixture("hi-IN-SwaraNeural")
    same["available_voices"].append(dict(same["available_voices"][0]))
    wrong=signed_region_fixture("hi-IN-SwaraNeural")
    wrong["available_voices"][0]["gender"]="Male"
    foreign=signed_region_fixture("hi-IN-SwaraNeural")
    foreign["available_voices"][0]["id"]="mr-IN-AarohiNeural"
    for catalog_response in (same,wrong,foreign):
        with pytest.raises(VoiceCatalogUnavailable):
            route_voice_selection(
                shop_id=SHOP,campaign_id=CAMPAIGN,locale="hi-IN",
                voice_id="hi-IN-SwaraNeural",
                current_editor=lambda *scope:True,user_confirmed_charge=True,
                read_verified_region_voices=lambda *scope:catalog_response)


def test_free_english_never_reads_azure_catalog_even_with_corrupt_callback():
    attempts=[]
    selected=route_voice_selection(
        shop_id=SHOP,campaign_id=CAMPAIGN,locale="en-us",
        voice_id="af_heart",current_editor=lambda *scope:True,
        user_confirmed_charge=False,
        read_verified_region_voices=lambda *scope:attempts.append(1) or
            {"region":"invalid"})
    assert selected["provider"]=="kokoro-onnx"
    assert selected["cost_reserved"] is False
    assert attempts==[]
