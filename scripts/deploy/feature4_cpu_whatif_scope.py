"""Validate exact already-existing DEV resources in ARM what-if Ignore.

No mutation, privilege change, ID/name logging or authorization of Create/Modify.
"""
import json
from pathlib import Path


def load_existing_dev_ids(path: Path, scope: str) -> frozenset[str]:
    if (not isinstance(scope, str)
            or not scope.startswith("/subscriptions/")
            or not scope.endswith("/resourcegroups/rg-retailgrowth-dev")):
        raise ValueError("unexpected DEV resource scope")
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not 1 <= len(data) <= 500:
        raise ValueError("invalid or unbounded DEV resource inventory")
    out = []
    for item in data:
        if not isinstance(item, str):
            raise ValueError("invalid resource inventory member")
        rid = item.lower()
        if (rid != rid.strip() or len(rid) > 2048
                or not rid.startswith(scope + "/providers/")
                or any(c in rid for c in "?#\r\n")):
            raise ValueError("foreign or malformed DEV resource ID")
        out.append(rid)
    if len(set(out)) != len(out):
        raise ValueError("duplicate DEV resource")
    return frozenset(out)


def is_existing_ignore(rid: str, action: str,
                       inventoried: frozenset[str], scope: str) -> bool:
    return (action == "Ignore"
            and isinstance(rid, str)
            and rid.startswith(scope + "/providers/")
            and rid in inventoried)


def verify_tagged_partial_plan(listed, plan, scope: str) -> bool:
    """Never adopt another worker plan: exact tag, RG, SKU, Linux and location."""
    if not isinstance(listed,list) or len(listed)>1:
        raise ValueError("ambiguous DEV CPU plan inventory")
    if not listed:
        if plan is not None:
            raise ValueError("unexpected CPU plan details")
        return False
    if not isinstance(plan,dict) or not isinstance(scope,str):
        raise ValueError("missing CPU plan proof")
    expected=scope.lower().rstrip("/")+"/providers/microsoft.web/serverfarms/rgai-dev-f4cpu-plan"
    tags={str(k).lower():str(v).lower() for k,v in (plan.get('tags') or {}).items()}
    sku=plan.get('sku') or {}
    if (str(plan.get('id') or '').lower()!=expected or
        str(listed[0].get('id') or '').lower()!=expected or
        tags.get('app')!='retailgrowthai' or tags.get('environment')!='dev' or
        tags.get('purpose')!='feature4-cpu-private-worker' or
        sku.get('name')!='FC1' or sku.get('tier')!='FlexConsumption' or
        str(plan.get('location') or '').lower()!='centralindia'):
        raise ValueError("foreign or misconfigured F4 CPU plan")
    return True


def verify_private_existing_container(existence, details) -> bool:
    """Accept only an authenticated, explicitly nonpublic existing blob container."""
    if not isinstance(existence,dict) or type(existence.get('exists')) is not bool:
        raise ValueError("unverified container presence")
    if not existence['exists']:
        if details is not None:
            raise ValueError("unexpected container details")
        return False
    if not isinstance(details,dict):
        raise ValueError("container missing private proof")
    # Azure CLI versions may expose the field at root or properties.
    access=details.get('publicAccess',(details.get('properties') or {}).get('publicAccess'))
    if access not in (None,'None','none'):
        raise ValueError("container is not private")
    if str(details.get('name') or '')!='retailgrowth-f4cpu-packages':
        raise ValueError("foreign package container")
    return True


def required_reuse_action(action, already_exists: bool) -> bool:
    """Never permit a what-if Modify/Delete or double Create of verified prior objects."""
    return type(already_exists) is bool and action==('NoChange' if already_exists else 'Create')
