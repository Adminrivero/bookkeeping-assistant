import json
from pathlib import Path
from src.rule_generator.schema import load_rule_schema, validate_instance

ALLOCATION_PATH = Path("config/allocation_rules.json")


def test_load_rule_schema():
    """Schema loads successfully and is a dict."""
    schema = load_rule_schema()
    assert isinstance(schema, dict)


def test_allocation_rules_conform_to_schema():
    """Validate the canonical allocation_rules.json against the rule schema."""
    assert ALLOCATION_PATH.exists(), f"Missing allocation rules: {ALLOCATION_PATH}"
    rules = json.loads(ALLOCATION_PATH.read_text(encoding="utf-8"))
    validate_instance(rules)


def test_example_legacy_rule_conforms_to_schema():
    """Sanity-check: a minimal legacy-style rule structure should validate."""
    example = {
        "_name": "example",
        "_version": "0.0.1",
        "_description": "Minimal legacy example for schema validation",
        "_scope": ["chequing_account"],
        "_rules": [
            {
                "category_name": "Office Expenses - Retail/Hardware",
                "transaction_type": "EXPENSE",
                "logic": "MUST_MATCH_ALL",
                "rules": [
                    {"field": "Description", "operator": "CONTAINS", "value": "HOME DEPOT"}
                ],
            }
        ],
    }
    validate_instance(example)