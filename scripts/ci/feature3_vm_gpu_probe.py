"""Azure GPU VM VM-family quota probe (read-only, no allocation).

SKU presence alone never authorizes VM creation. Need regional vCPU limit,
exact GPU family vCPU limit and unrestricted SKU *all at once*. Returned
eligibility is only a deploy-review hint; capacity/pricing remain unverified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


CANDIDATES = {
 "Standard_NC4as_T4_v3": {"vcpus": 4, "family": ("ncast4",)},
 "Standard_NV6ads_A10_v5": {"vcpus": 6, "family": ("nvads", "a10")},
}


def capacity(usage: object, skus: object, region: str) -> dict:
    if region not in ("eastus", "centralindia") or not isinstance(usage, list) or not isinstance(skus, list):
        raise ValueError("Read-only Azure VM inventory invalid")
    rows = []
    for item in usage:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or {}
        texts = [name.get("value", ""), name.get("localizedValue", "")] if isinstance(name, dict) else [str(name)]
        try:
            limit, used = int(item.get("limit")), int(item.get("currentValue"))
        except (TypeError, ValueError):
            continue
        if min(limit, used) < 0 or used > limit:
            continue
        rows.append((" ".join(texts).replace(" ", "").replace("_", "").lower(),limit-used))
    reg = next((v for n,v in rows if ("totalregionalvcpus" in n or "totalregionalcores" in n)),0)
    answer = []
    for sku, info in CANDIDATES.items():
        matched = []
        for n,remaining in rows:
            if "family" not in n:
                continue
            if all(token in n for token in info["family"]):
                matched.append(remaining)
        matched_skus = [s for s in skus if isinstance(s,dict) and s.get("name")==sku]
        available_sku = (len(matched_skus)==1 and
          not (matched_skus[0].get("restrictions") or []))
        quota = min(matched) if matched else 0
        answer.append({"sku":sku,"region":region,"required_vcpus":info["vcpus"],
          "regional_vcpus_remaining":reg,"gpu_family_vcpus_remaining":quota,
          "sku_unrestricted":available_sku,
          "passes_quota_for_review": bool(available_sku and
              quota>=info["vcpus"] and reg>=info["vcpus"]),
          "vm_created":False,"price_verified":False})
    return {"region":region,"gpu_vm_candidates":answer,"read_only":True}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--usage",type=Path,required=True)
    p.add_argument("--skus",type=Path,required=True)
    p.add_argument("--region",choices=("centralindia","eastus"),required=True)
    a=p.parse_args(argv)
    try:
        report=capacity(json.loads(a.usage.read_text()),json.loads(a.skus.read_text()),a.region)
    except (ValueError,OSError,UnicodeError) as exc:
        print("BLOCKED: unable to validate GPU VM inventory: "+str(exc))
        return 3
    print(json.dumps(report,sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
