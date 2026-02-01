import json
from pathlib import Path
import pytest
import jsonschema
from jsonschema.validators import validator_for

SCHEMA_PATH = Path("config/schemas/rule_schema.json")
ALLOCATION_PATH = Path("config/allocation_rules.json")


def _validate_instance(schema: dict, instance: dict):
    Validator = validator_for(schema)
    Validator.check_schema(schema)
    validator = Validator(schema)
    errors = list(validator.iter_errors(instance))
    if errors:
        msgs = []
        for e in errors:
            loc = ".".join(str(p) for p in e.path) or "<root>"
            msgs.append(f"{loc}: {e.message}")
        pytest.fail("Schema validation errors:\n" + "\n".join(msgs))


def test_allocation_rules_conform_to_schema():
    """Validate the canonical allocation_rules.json against the rule schema."""
    assert SCHEMA_PATH.exists(), f"Missing schema: {SCHEMA_PATH}"
    assert ALLOCATION_PATH.exists(), f"Missing allocation rules: {ALLOCATION_PATH}"

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    rules = json.loads(ALLOCATION_PATH.read_text(encoding="utf-8"))

    _validate_instance(schema, rules)


def test_example_legacy_rule_conforms_to_schema():
    """Sanity-check: a minimal legacy-style rule structure should validate."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
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

    _validate_instance(schema, example)