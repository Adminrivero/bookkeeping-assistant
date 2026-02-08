import json
from pathlib import Path
from typing import Dict, Any

from src.rule_generator.rules_io import load_rules, save_rules


def _sample_rules(include_metadata: bool = False) -> Dict[str, Any]:
    rule: Dict[str, Any] = {
        "category_name": "Office Expenses - Retail/Hardware",
        "transaction_type": "EXPENSE",
        "logic": "MUST_MATCH_ALL",
        "rules": [
            {"field": "Description", "operator": "CONTAINS", "value": "HOME DEPOT"}
        ],
    }
    if include_metadata:
        rule.update({"rule_id": "alpha", "priority": 5, "scope": "td_visa"})

    return {
        "_name": "sample",
        "_version": "0.0.1",
        "_description": "Sample rules for IO tests",
        "_scope": ["chequing_account"],
        "_rules": [rule],
    }


def test_load_rules_reads_allocation_rules():
    rules = load_rules()
    assert isinstance(rules, dict)
    assert "_rules" in rules
    assert isinstance(rules["_rules"], list)
    assert len(rules["_rules"]) > 0


def test_save_and_load_round_trip_preserves_structure(tmp_path: Path):
    rules_path = tmp_path / "rules.json"
    rules = _sample_rules()
    save_rules(rules, path=rules_path)

    loaded = load_rules(rules_path)
    assert loaded == rules


def test_metadata_fields_preserved(tmp_path: Path):
    rules_path = tmp_path / "rules.json"
    rules = _sample_rules(include_metadata=True)
    save_rules(rules, path=rules_path)

    loaded = load_rules(rules_path)
    saved_rule = loaded["_rules"][0]
    assert saved_rule["rule_id"] == "alpha"
    assert saved_rule["priority"] == 5
    assert saved_rule["scope"] == "td_visa"


def test_save_rules_rejects_invalid_when_validation_requested(tmp_path: Path):
    rules_path = tmp_path / "rules.json"
    invalid_rules = {
        "_version": "0.0.1",
        "_description": "missing name",
        "_scope": ["chequing_account"],
        "_rules": [],
    }

    result = save_rules(invalid_rules, path=rules_path, validate_before_save=True)
    assert result is not None
    assert result["valid"] is False
    assert not rules_path.exists()


def test_save_rules_allows_valid_when_validation_requested(tmp_path: Path):
    rules_path = tmp_path / "rules.json"
    rules = _sample_rules()

    result = save_rules(rules, path=rules_path, validate_before_save=True)
    assert result is not None
    assert result["valid"] is True
    assert rules_path.exists()

    loaded = load_rules(rules_path)
    assert loaded == rules
