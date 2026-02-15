import json
from pathlib import Path

import pytest

from tests.rule_generator import harness


def test_valid_rules_pass_schema_validation():
    for rule in harness.load_valid_rules():
        result = harness.validate_rule(rule)
        assert result["valid"], result["errors"]


def test_invalid_rules_fail_schema_validation():
    invalid = harness.load_invalid_rules()
    for rule in invalid:
        result = harness.validate_rule(rule)
        assert result["valid"] is False
        assert result["errors"]


def test_edge_cases_are_schema_valid():
    for rule in harness.load_edge_case_rules():
        result = harness.validate_rule(rule)
        assert result["valid"], result["errors"]


def test_evaluation_matches_expected_transactions():
    transactions = harness.load_canonical_transactions()
    valid_rules = harness.load_valid_rules()

    # Home Depot rule should match first transaction only
    report = harness.run_evaluation(valid_rules[0], transactions, expected_matches=[0])
    assert len(report["matches"]) == 1
    assert report["false_positives"] == []
    assert report["false_negatives"] == []

    # Fuel group rule should match fuel transactions (indexes 1 and 6)
    report = harness.run_evaluation(valid_rules[1], transactions, expected_matches=[1, 6])
    assert len(report["matches"]) == 2


def test_round_trip_rules_preserves_structure(tmp_path: Path):
    rules_doc = {
        "_name": "roundtrip",
        "_version": "0.0.1",
        "_description": "test round trip",
        "_scope": ["chequing_account"],
        "_rules": harness.load_valid_rules()[:2],
    }

    reloaded = harness.round_trip_rules(rules_doc)
    assert reloaded == rules_doc


def test_transactions_fixture_shape():
    txs = harness.load_canonical_transactions()
    assert len(txs) >= 10
    for tx in txs:
        assert "Description" in tx
        assert "Debit" in tx
        assert "Credit" in tx


@pytest.mark.parametrize("fixture_path", [
    harness.TRANSACTIONS_PATH,
    harness.VALID_RULES_PATH,
    harness.INVALID_RULES_PATH,
    harness.EDGE_RULES_PATH,
])
def test_fixture_files_exist(fixture_path: Path):
    assert fixture_path.exists()
    assert fixture_path.read_text(encoding="utf-8")
