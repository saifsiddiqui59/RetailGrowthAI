"""Cross-feature references and user-away/cost policies are complete and fail closed."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REFS=json.loads((ROOT/"coordination/shared_feature_references.json").read_text())
POLICY=json.loads((ROOT/"coordination/feature_test_policy.json").read_text())
DAG=json.loads((ROOT/"coordination/dependencies.json").read_text())

def test_exact_five_chat_names_and_source_work_sizes():
    assert {v["feature"]:v["chat_name"] for v in REFS["feature_chats"]} == {
        "2":"reail feature2","3":"retail feature 3","4":"retail feature 4",
        "5":"retail feature 5","7":"retail feature 7"}
    assert sum(v["task_count"] for v in REFS["feature_chats"])==159
    assert POLICY["feature_chat_names"]=={x["feature"]:x["chat_name"] for x in REFS["feature_chats"]}

def test_all_cross_feature_ids_are_real_immutable_handoff_nodes():
    deps={v["id"] for v in DAG["tasks"]}
    assert len(REFS["reference_edges"])>=8
    assert all(set(e["dependency_ids"])<=deps for e in REFS["reference_edges"])
    assert all(e["producer"]!=e["consumer"] for e in REFS["reference_edges"])

def test_no_samples_gpu_prod_or_paid_model_dispatch():
    assert POLICY["ten_hour_user_absence"]["no_user_facing_samples"]
    assert POLICY["ten_hour_user_absence"]["no_sample_image_video_reel_or_preview_generation"]
    assert not POLICY["cost_policy"]["paid_gpu_inference_allowed"]
    assert not POLICY["cost_policy"]["paid_model_agents_allowed"]
    assert not POLICY["cost_policy"]["prod_deploy"]
    assert not POLICY["cost_policy"]["wine_shop_pos_mutation"]
    assert not POLICY["cost_policy"]["gpt_4_1_mini"]["auto_invoke"]
    assert POLICY["cost_policy"]["gpt_4_1_mini"]["max_calls_per_task"]==1

def test_auth_accounts_uncreated_and_no_secret_creds_in_config():
    assert POLICY["supabase"]["project_ref"]=="jeearzffnjbvghwjjjrf"
    assert len(POLICY["supabase"]["test_accounts"])==2
    assert all(account["auth_created"] is False for account in POLICY["supabase"]["test_accounts"])
    raw=json.dumps(POLICY).lower()
    assert "SUPABASE_SERVICE_ROLE_KEY" not in raw
    assert "SUPABASE_SERVICE_ROLE_KEY" not in raw
    assert POLICY["supabase"]["shop_membership"]
