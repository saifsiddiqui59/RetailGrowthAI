"""Only sanitized, read-only Operations telemetry can leave the P0 DEV run."""
from pathlib import Path
S=Path(__file__).resolve().parents[2]/".github/workflows/p1-dev-rpc-exception-classifier-once.yml"


def test_exact_dev_oidc_and_one_shot_gate():
    s=S.read_text()
    for x in ("branches: [main]","environment: dev",
              "rg-retailgrowth-dev","rgai-dev-functions-d4e5ddbd",
              "rgai-dev-law","centralindia",
              "audit(dev): classify RetailGrowthAI Flex RPC exception sources",
              "P0_RPC_DEV_SCOPE_VERIFIED=true"):
        assert x in s,x


def test_no_raw_exception_text_customer_or_secret_exposure():
    s=S.read_text()
    for x in ("AppExceptions","AppTraces","AppRequests",
              "summarize n=count()", "ExceptionType", "P0_NO_RAW_AZURE_LOG_VALUES_EXPORTED=true"):
        assert x in s,x
    for prohibited in (
        "az functionapp config appsettings set", "az functionapp deployment",
        "az group create", "az storage account create", "az monitor log-analytics workspace create",
        "supabase db push","apply_migration","RGAI_DEV_SERVICE_KEY",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY","print(ExceptionMessage)",
        "project Message", "project OuterMessage",
    ):
        assert prohibited not in s,prohibited
