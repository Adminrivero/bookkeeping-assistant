import json
from pathlib import Path

from src.rule_generator.schema import (
    ValidationIssue,
    load_rule_schema,
    validate_rule_block,
    validate_rules_document,
)

ALLOCATION_PATH = Path("config/allocation_rules.json")


def _assert_has_error(errors: list[ValidationIssue], needle: str) -> bool:
    return any(needle in issue["message"] or needle in issue["path"] for issue in errors)


def test_load_rule_schema():
    """Schema loads successfully and includes the rule items fragment."""
    schema = load_rule_schema()
    assert isinstance(schema, dict)
    assert "_rules" in schema["properties"]


def test_allocation_rules_conform_to_schema():
    """Validate the canonical allocation_rules.json against the rule schema."""
    assert ALLOCATION_PATH.exists(), f"Missing allocation rules: {ALLOCATION_PATH}"
    rules = json.loads(ALLOCATION_PATH.read_text(encoding="utf-8"))
    result = validate_rules_document(rules)
    assert result["valid"], result["errors"]


def test_valid_rule_block_passes():
    rule = {
        "category_name": "Office Expenses - Retail/Hardware",
        "transaction_type": "EXPENSE",
        "logic": "MUST_MATCH_ALL",
        "rules": [
            {"field": "Description", "operator": "CONTAINS", "value": "HOME DEPOT"}
        ],
    }
    result = validate_rule_block(rule)
    assert result["valid"] is True
    assert result["errors"] == []


def test_rule_missing_required_field_reports_error():
    rule = {
        "category_name": "Office Expenses - Retail/Hardware",
        # transaction_type missing
        "logic": "MUST_MATCH_ALL",
        "rules": [
            {"field": "Description", "operator": "CONTAINS", "value": "HOME DEPOT"}
        ],
    }
    result = validate_rule_block(rule)
    assert result["valid"] is False
    assert _assert_has_error(result["errors"], "transaction_type")


def test_rule_with_invalid_operator_surfaces_path():
    rule = {
        "category_name": "Office Expenses - Retail/Hardware",
        "transaction_type": "EXPENSE",
        "logic": "MUST_MATCH_ALL",
        "rules": [
            {"field": "Description", "operator": "BAD_OPERATOR", "value": "HOME DEPOT"}
        ],
    }
    result = validate_rule_block(rule)
    assert result["valid"] is False
    assert _assert_has_error(result["errors"], "/rules/0/operator")
    assert _assert_has_error(result["errors"], "BAD_OPERATOR")


def test_rules_document_missing_name_surfaces_error():
    document = {
        # _name missing on purpose
        "_version": "0.0.1",
        "_description": "Missing name should fail",
        "_scope": ["chequing_account"],
        "_rules": [],
    }
    result = validate_rules_document(document)
    assert result["valid"] is False
    assert _assert_has_error(result["errors"], "_name")