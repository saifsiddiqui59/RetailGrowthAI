import pytest
from ai_agents.feature2_speech_catalog import (
    published_voices_in_region, VoiceCatalogUnavailable,
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
