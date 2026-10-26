"""Feature2 AI cost-ledger contract and backend-only RPC facade tests."""
from pathlib import Path
import runpy
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "azure-functions/campaign-api"
sys.path.insert(0, str(SOURCE))
Store = runpy.run_path(str(SOURCE / "feature2_ai_budget_store.py"))["Feature2BudgetStore"]
SQL = (ROOT / "supabase/migrations/20261026194000_feature2_ai_cost_ledger.sql").read_text()
SHOP = "a1000000-0000-4000-8000-000000000001"
ACTOR = "a1000000-0000-4000-8000-000000000002"
RECEIPT = "a1000000-0000-4000-8000-000000000003"


class FakeAdmin:
    def __init__(self, receipt=RECEIPT, settled=True):
        self.calls = []
        self.receipt = receipt
        self.settled = settled
    def request(self, path, **kwargs):
        self.calls.append((path, kwargs))
        return self.receipt if "reserve" in path else self.settled


def test_server_reservation_passes_exact_verified_ids_and_rounded_up_cap():
    admin = FakeAdmin()
    budget = Store(admin)
    assert budget.reserve(shop_id=SHOP, actor_id=ACTOR, operation="prompt",
        max_cost_usd=0.0000011, request_id=RECEIPT) == RECEIPT
    path, args = admin.calls[0]
    assert path == "rpc/feature2_reserve_ai_budget"
    assert args["method"] == "POST"
    assert args["data"] == {
        "p_shop_id": SHOP, "p_actor_id": ACTOR,
        "p_operation": "prompt", "p_upper_cost_usd": "0.000002",
        "p_request_id": RECEIPT,
    }
    budget.settle(reservation_id=RECEIPT, actual_cost_usd=0.000001)
    assert admin.calls[1][0] == "rpc/feature2_settle_ai_budget"
    assert admin.calls[1][1]["data"]["p_actual_usd"] == "0.000001"


@pytest.mark.parametrize("bad", [0,-1,0.5,float("nan"),float("inf"),"not money"])
def test_invalid_cost_never_calls_database(bad):
    admin=FakeAdmin()
    with pytest.raises(ValueError):
        Store(admin).reserve(shop_id=SHOP, actor_id=ACTOR,
             operation="campaign_copy", max_cost_usd=bad)
    assert admin.calls==[]


def test_invalid_shop_or_actor_or_operation_never_reserves():
    admin=FakeAdmin()
    budget=Store(admin)
    with pytest.raises(ValueError):
        budget.reserve(shop_id="foreign",actor_id=ACTOR,
                       operation="prompt",max_cost_usd=0.002)
    with pytest.raises(ValueError):
        budget.reserve(shop_id=SHOP,actor_id="anonymous",
                       operation="prompt",max_cost_usd=0.002)
    with pytest.raises(ValueError):
        budget.reserve(shop_id=SHOP,actor_id=ACTOR,
                       operation="admin_override",max_cost_usd=0.002)
    assert admin.calls==[]


def test_ambiguous_reservation_or_settlement_never_blindly_retries():
    from tenant_store import StorageUnavailable
    a=FakeAdmin(receipt=None)
    with pytest.raises(StorageUnavailable):
        Store(a).reserve(shop_id=SHOP, actor_id=ACTOR,
                         operation="prompt", max_cost_usd=0.003)
    assert len(a.calls)==1
    b=FakeAdmin(settled=False)
    with pytest.raises(StorageUnavailable):
        Store(b).settle(reservation_id=RECEIPT,actual_cost_usd=0.001)
    assert len(b.calls)==1


def test_migration_is_default_off_and_service_only():
    assert "enabled boolean not null default false" in SQL
    assert "period_cap_usd numeric(10,6) not null default 0" in SQL
    assert "enable row level security" in SQL
    assert "grant all on public.shop_ai_budget_controls to service_role" in SQL
    assert "grant all on public.shop_ai_spend_reservations to service_role" in SQL
    assert "from public,anon,authenticated" in SQL
    assert "grant execute on function public.feature2_reserve_ai_budget" in SQL
    assert "grant execute on function public.feature2_settle_ai_budget" in SQL
    assert "where s.shop_id=p_shop_id for update" in SQL
    assert "m.role in ('OWNER','EDITOR')" in SQL
    assert "used_count>=max_count" in SQL
    assert "usage_usd+bounded_cost>approval.period_cap_usd" in SQL
    assert "ai_unique_request_per_shop unique(shop_id,request_id)" in SQL
    assert "AI_REQUEST_ALREADY_RESERVED" in SQL
    assert "pg_catalog.ceil(p_upper_cost_usd * 1000000)" in SQL
    assert "shop_ai_spend_reservations" in SQL
    assert "RG003" in SQL and "RG004" in SQL
    assert "references public.shops(id) on delete cascade" in SQL
