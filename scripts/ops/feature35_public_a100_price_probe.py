"""Public no-subscription Azure Retail Prices A100 meter discovery.

Only source-provided rates are returned. NEVER treats estimates as a signed
Azure customer contract, fixed all-in charge, or approval to start a GPU.
"""
from __future__ import annotations
import json
import urllib.parse
import urllib.request

API = "https://prices.azure.com/api/retail/prices"
MAX_PAGES = 8

def discover(fetch=None):
    if fetch is None:
        def fetch(url):
            with urllib.request.urlopen(url, timeout=25) as r:
                if r.status != 200: raise ValueError("Retail pricing HTTP status")
                return json.load(r)
    filter_value = "serviceName eq 'Azure Container Apps' and armRegionName eq 'eastus' and priceType eq 'Consumption'"
    url = API + "?" + urllib.parse.urlencode({"$filter":filter_value})
    matches = []
    other_active = []
    for page in range(MAX_PAGES):
        obj = fetch(url)
        if not isinstance(obj,dict) or not isinstance(obj.get("Items"),list):
            raise ValueError("Invalid public Azure price API response")
        for p in obj["Items"]:
            if p.get("armRegionName")!="eastus" or p.get("serviceName")!="Azure Container Apps":
                continue
            name=" ".join(str(p.get(k,"")) for k in ("meterName","skuName","productName"))
            category=matches if ("A100" in name.upper() or "NC A100" in name.upper()) else other_active
            if category is other_active and not ("vCPU" in name or "Memory" in name or "RAM" in name or "GPU" in name):
                continue
            # Preserve published meter ID/units exactly; no invented USD/sec.
            category.append({k:p.get(k) for k in ("armRegionName","serviceName","productName","skuName","meterName",
                         "meterId","unitOfMeasure","currencyCode","retailPrice","effectiveStartDate","type")})
        nexturl=obj.get("NextPageLink")
        if not nexturl:
            break
        target = urllib.parse.urlsplit(nexturl) if isinstance(nexturl,str) else None
        if not target or target.scheme != "https" or target.hostname != "prices.azure.com" or target.path != "/api/retail/prices":
            raise ValueError("Invalid or external continuation URL")
        url=nexturl
    return {"region":"eastus","service":"Azure Container Apps",
            "official_public_a100_meters":matches,
            "supporting_compute_meters":other_active[:24],
            "pages_checked":page+1,
            "pagination_complete":not bool(nexturl),
            "is_customer_contract_quote":False,
            "paid_gpu_start_authorized":False}

def main():
    result=discover()
    print("AZURE_PUBLIC_PRICE_EVIDENCE="+json.dumps(result,sort_keys=True))
    if not result["official_public_a100_meters"]:
        print("NO_VERIFIED_EASTUS_A100_RETAIL_METER; PAID_START_REMAINS_BLOCKED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
