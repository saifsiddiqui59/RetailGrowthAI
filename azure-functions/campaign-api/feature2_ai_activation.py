"""Trusted Feature2 model activation. No browser-controlled model, price or budget.

This module cannot enable model spending: the operator has to (1) enable a
server-only flag, (2) configure a permitted Azure Foundry deployment and
price, (3) separately apply the reviewed budget RPC migration, and (4) approve
a positive per-shop budget in the database. Any missing gate fails closed.
"""
from __future__ import annotations

from functools import partial

from ai_agents.feature2_ai_writer import AzureFeature2ContentLLM, create_ai_content_draft
from ai_agents.feature2_llm import AzureFeature2PromptLLM
from ai_agents.prompt_improver import improve_prompt
from ai_agents.providers import FoundryUnavailable
from feature2_ai_budget_store import Feature2BudgetStore
from tenant_store import StorageUnavailable, canonical_uuid


class Feature2AiActivation:
    def __init__(
        self, admin, *, endpoint: str, deployment: str, api_key: str,
        input_usd_per_million: float, output_usd_per_million: float,
        approved_max_cost_usd: float, transport=None,
    ):
        self.budget = Feature2BudgetStore(admin)
        self.options = {
            "endpoint": endpoint, "deployment": deployment, "api_key": api_key,
            "input_usd_per_million": input_usd_per_million,
            "output_usd_per_million": output_usd_per_million,
            "approved_max_cost_usd": approved_max_cost_usd,
        }
        if transport is not None:
            self.options["transport"] = transport
        if (not isinstance(approved_max_cost_usd, (int,float))
            or not 0 < approved_max_cost_usd <= 0.05):
            raise ValueError("Real AI cap must be positive and at most USD 0.05")

    def _reserve_factory(self, shop_id: str, actor_id: str, operation: str, receipt: list[str], request_id: str | None = None):
        sid, uid = canonical_uuid(shop_id), canonical_uuid(actor_id)
        def reserve(max_cost_usd: float) -> str:
            if receipt:
                raise RuntimeError("Cannot reserve twice for one AI attempt")
            token = self.budget.reserve(
                shop_id=sid, actor_id=uid, operation=operation,
                max_cost_usd=max_cost_usd, request_id=request_id)
            receipt.append(token)
            return token
        return reserve

    def _settle_if_billed(self, model, receipt: list[str]) -> None:
        if receipt and model.last_usage is not None:
            self.budget.settle(
                reservation_id=receipt[0],
                actual_cost_usd=model.last_usage["actual_cost_usd"])

    def improve(self, *, original_prompt, retailer, output_formats, language,
                shop_id, actor_id):
        receipt = []
        model = AzureFeature2PromptLLM(
            **self.options,
            reserve_cost=self._reserve_factory(shop_id, actor_id, "prompt", receipt))
        try:
            result = improve_prompt(
                original_prompt, retailer, output_formats=output_formats,
                language=language, provider_mode="approved_llm", provider=model,
                explicit_cost_approval=True, subscription_quota_ok=True,
                approved_cost_limit_usd=self.options["approved_max_cost_usd"],
                environ={"RETAIL_PROMPT_LLM_ENABLED": "true"})
            if model.last_usage is None:
                raise FoundryUnavailable("Missing real model token accounting")
            result["usage"] = {
                "paid_inference_calls": 1, "provider": "azure_foundry",
                "actual_paid_cost_usd": model.last_usage["actual_cost_usd"],
                "prompt_tokens": model.last_usage["prompt_tokens"],
                "completion_tokens": model.last_usage["completion_tokens"],
                "approved_max_cost_usd": self.options["approved_max_cost_usd"],
            }
            return result
        except (StorageUnavailable, PermissionError, FoundryUnavailable):
            raise
        except Exception as exc:
            raise FoundryUnavailable("Approved prompt inference could not be reviewed") from exc
        finally:
            # Model may have billed even if a subsequent content validation
            # fails. Settlement is based on usage, not UI acceptance.
            self._settle_if_billed(model, receipt)

    def draft(self, *, brief, retailer, campaign_id, now, trend, shop_id, actor_id, request_id=None):
        receipt = []
        model = AzureFeature2ContentLLM(
            **self.options,
            reserve_cost=self._reserve_factory(shop_id, actor_id, "campaign_copy", receipt, request_id))
        try:
            result = create_ai_content_draft(
                brief, retailer, campaign_id=campaign_id, now=now, trend=trend,
                copy_provider=model,
                explicit_cost_approval=True, subscription_quota_ok=True,
                approved_cost_limit_usd=self.options["approved_max_cost_usd"],
                environ={"RETAIL_FEATURE2_CONTENT_LLM_ENABLED": "true"})
            if model.last_usage is None:
                raise FoundryUnavailable("Missing real AI model token usage")
            result["model_usage"] = {
                "provider": "azure_foundry",
                "paid_inference_calls": 1,
                "actual_paid_cost_usd": model.last_usage["actual_cost_usd"],
                "prompt_tokens": model.last_usage["prompt_tokens"],
                "completion_tokens": model.last_usage["completion_tokens"],
            }
            return result
        except (StorageUnavailable, PermissionError, FoundryUnavailable):
            raise
        except Exception as exc:
            raise FoundryUnavailable("AI draft inference or editorial review failed") from exc
        finally:
            self._settle_if_billed(model, receipt)
