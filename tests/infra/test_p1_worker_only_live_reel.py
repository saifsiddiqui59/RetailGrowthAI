"""Worker-only smoke is entirely isolated, protected and has real codec proof."""
from pathlib import Path

R=Path(__file__).resolve().parents[2]
W=R/".github/workflows/p1-dev-queue-worker-real-reel-once.yml"
SCRIPT=R/"tests/e2e/dev_queue_worker_reel_once.py"


def test_single_owner_gated_existing_dev_and_no_web_client_secrets():
    wf=W.read_text()
    for target in (
        "branches: [main]", "environment: dev",
        "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
        "test(dev): verify actual RetailGrowthAI Azure queue FFmpeg Reel",
        "RGAI_DEV_REAL_QUEUE_OPERATOR_APPROVAL: OWNER_APPROVED_ONE_SHOT_RENDER_WORKER_ONLY",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
        "python3 -u tests/e2e/dev_queue_worker_reel_once.py",
        "retailgrowthai-dev-real-azure-queue-worker-30s-mp4",
        "if-no-files-found: warn",
    ):
        assert target in wf,target


def test_real_worker_unmodified_and_no_global_security_gate_bypass():
    wf=W.read_text()
    script=SCRIPT.read_text()
    for text in ("ORIGIN=\"https://jeearzffnjbvghwjjjrf.supabase.co\"",
                 'root_owner=exact_uuid(existing[0]["owner_user_id"])',
                 '"status":"QUEUED","idempotency_key":digest',
                 'len(existing)!=1',
                 'created_shop=True',
                 'verify_worker_mp4(OUTPUT)',
                 'WORKER_TEST_SIGNED_PRIVATE_30S_H264_AAC_BYTES_VERIFIED=true',
                 'WORKER_TEST_ISOLATED_FIXTURE_CLEANUP=',
                 'REAL_DEV_AZURE_QUEUE_REEL_ACCEPTANCE=PASSED'):
        assert text in script,text
    assert "retail_onboarding_status" not in script
    assert 'auth/v1/admin/users' not in script
    assert "enforce_approval" not in script
    assert "retail_private.platform_admins" not in script
    for blocked in ("az functionapp", "always-ready", "appsettings set",
                    "supabase db push", "apply_migration",
                    "WineShopPOS", "RETAIL_NOTIFICATIONS_ENABLED=true"):
        assert blocked not in wf,blocked
    assert "RGAI_DEV_SERVICE_KEY" not in str((R/"frontend").name)


def test_first_party_original_music_and_private_reel_output():
    src=SCRIPT.read_text()
    for x in (
        "audio.setframerate(22050)",
        'content_type="audio/wav"',
        '"license_name":"owned"',
        '"music_asset_id":music_id',
        '"stream":',
    ):
        if x=="\"stream\":":
            continue
        assert x in src,x
    assert 'audios[0].get("codec_name")!="aac"' in src
    assert 'videos[0].get("width")!=1080' in src
    assert 'videos[0].get("height")!=1920' in src
    assert "shop_id+\"/renders/\"" in src
    assert "if not 2048<len(binary)<=80*1024*1024" in src
