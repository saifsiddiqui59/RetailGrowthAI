"""Static audit: OIDC Foundry readiness check must remain free/read-only."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/'.github/workflows/retail-dev-feature2-foundry-readonly-once.yml'
SOURCE=WORKFLOW.read_text()


def test_only_approved_main_merge_triggers_exact_existing_dev_readiness():
    assert "branches: [main]" in SOURCE
    assert ".github/workflows/retail-dev-feature2-foundry-readonly-once.yml" in SOURCE
    assert "workflow_dispatch:" not in SOURCE
    assert "startsWith(github.event.head_commit.message, 'chore(feature2): inspect existing Azure Foundry readiness without provisioning')" in SOURCE
    assert "environment: dev" in SOURCE
    assert "id-token: write" in SOURCE
    assert "rg-retailgrowth-dev" in SOURCE
    assert "rgai-dev-functions-d4e5ddbd" in SOURCE
    assert "rgai-dev-openai-d4e5ddbd" in SOURCE
    assert "rgai-gpt-41-mini" in SOURCE
    assert "tags.get('environment')=='dev'" in SOURCE
    assert "az account show --query id" in SOURCE


def test_azure_cli_is_read_only_and_never_reads_key_values():
    commands=[
        line.strip() for line in SOURCE.splitlines()
        if line.lstrip().startswith("az ")
    ]
    assert commands
    permitted={"show","list","logout"}
    assert all((line.split()[2] if line.startswith("az account ") else
                line.split()[2] if line.startswith("az group ") else
                line.split()[4] if line.startswith("az cognitiveservices account deployment ") else
                line.split()[3] if line.startswith("az cognitiveservices account ") else
                line.split()[4] if line.startswith("az functionapp config appsettings ") else
                line.split()[2] if line.startswith("az functionapp ") else
                line.split()[1]) in permitted for line in commands)
    assert not any(re.search(r"\baz\s+.*\b(create|delete|update|set|keys)\b",line)
                   for line in commands)
    assert "account keys list" not in SOURCE
    assert "api-key" not in SOURCE
    assert "AZURE_FUNCTIONS_MODEL_INFERENCE" not in SOURCE
    assert "FEATURE2_READONLY_PAID_MODEL_INFERENCE=NOT_ATTEMPTED" in SOURCE
    assert "FEATURE2_READONLY_DEPLOYMENT_MUTATIONS=NONE" in SOURCE


def test_only_setting_names_are_collected_not_secret_values():
    assert "appsettings list -g" in SOURCE
    assert "--query '[].name'" in SOURCE
    assert "FEATURE2_READONLY_MISSING_SETTING_NAMES=" in SOURCE
    assert not re.search(r"--query [^\n]*(?:\.value|\.key1)", SOURCE)
