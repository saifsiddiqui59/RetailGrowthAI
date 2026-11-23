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
