"""Existing ROOT DEV shop is immutable; only owned nonce child records are created."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"tests/e2e/dev_existing_owner_shop_reel_once.py"
FLOW=ROOT/".github/workflows/p1-dev-owner-empty-shop-reel-once.yml"


def test_no_auth_signup_no_shop_insert_delete_or_root_configuration_changes():
    s=SOURCE.read_text()
    tree=ast.parse(s)
    assert 'shop_id=exact_uuid(existing[0]["id"])' in s
    assert 'WORKER_TEST_EMPTY_APPROVED_DEV_SHOP_VERIFIED=true' in s
    assert 'if existing_rows:' in s
    assert 'shop_id+"/uploads/"+aid+".png"' in s
    assert 'WORKER_TEST_ISOLATED_FIXTURE_CLEANUP=' in s
    assert 'REAL_DEV_AZURE_QUEUE_REEL_ACCEPTANCE=PASSED' in s
    for disallowed in (
        'table("shops",method="POST"',
        'table("shops",method="DELETE"',
        'table("shop_memberships",method="DELETE"',
        'table("shop_subscriptions",method="DELETE"',
        'auth/v1/admin/users', 'enforce_approval', 'set_config(',
        'update public.shops', 'RETAIL_NOTIFICATIONS_ENABLED=true',
    ):
        assert disallowed not in s,disallowed
    assert any(isinstance(node,ast.FunctionDef) and node.name=="main" for node in tree.body)


def test_cleanup_identified_by_created_ids_only_and_real_video_approval():
    s=SOURCE.read_text()
    for required in (
        '("render_jobs",{"id":"eq."+jid,"shop_id":"eq."+shop_id})',
        '("campaign_days",{"id":"eq."+did,"shop_id":"eq."+shop_id})',
        '("campaigns",{"id":"eq."+cid,"shop_id":"eq."+shop_id})',
        '("shop_usage_reservations",',
        'job_id":"in.("+cid+","+jid+")',
        '"music_asset_id":music_id',
        'audios[0].get("codec_name")!="aac"',
        'videos[0].get("codec_name")!="h264"',
        'verify_worker_mp4(OUTPUT)',
    ):
        assert required in s,required


def test_protected_one_shot_no_new_azure_resources():
    s=FLOW.read_text()
    for required in (
        "branches: [main]", "environment: dev",
        "test(dev): verify RetailGrowthAI FFmpeg in existing empty approved DEV shop",
        "OWNER_APPROVED_ONE_SHOT_RENDER_WORKER_ONLY",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
        "tests/e2e/dev_existing_owner_shop_reel_once.py",
        "retailgrowthai-dev-approved-root-shop-real-ffmpeg-30s-mp4",
        "if-no-files-found: warn",
    ):
        assert required in s,required
    for forbidden in (
        "az functionapp", "supabase db push", "apply_migration",
        "appsettings set", "WineShopPOS",
        "RETAIL_NOTIFICATIONS_ENABLED=true",
    ):
        assert forbidden not in s,forbidden
