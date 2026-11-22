"""Fail-closed, static contract for the non-mutating DEV release inventory."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / "supabase" / "candidates" / "feature4_cpu_dev_readonly_preflight_20261122.sql"


def test_feature4_dev_inventory_is_readonly_and_stage_pinned():
    source = SQL.read_text(encoding="utf-8")
    statement = "\n".join(line.split("--", 1)[0] for line in source.splitlines()).strip()
    assert statement.lower().startswith("with checks(")
    assert statement.endswith(";") and statement.count(";") == 1
    assert not re.search(r"\b(insert|update|delete|drop|alter|grant|revoke|truncate|execute|create|call|copy)\b", statement, re.I)
    assert "jeearzffnjbvghwjjjrf" in source
    assert statement.count("('required table ") == 8
    assert statement.count("('required routine ") == 3
    assert statement.count("('unapplied ") == 9
    assert "expected_present is not distinct from observed_present" in statement
    assert "quota render operation constraint" in statement
    assert "media GENERATED source constraint" in statement
