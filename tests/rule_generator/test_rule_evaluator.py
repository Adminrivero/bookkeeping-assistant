from src.rule_generator.rule_evaluator import evaluate_rule


CANONICAL_BASE = {
    "Date": "2025-01-01",
    "Description": "",
    "Debit": 0.0,
    "Credit": 0.0,
    "Balance": None,
    "source": "test_source",
}


def _tx(**overrides):
    tx = CANONICAL_BASE.copy()
    tx.update(overrides)
    return tx


def test_contains_any_matches_expected():
    rule = {
        "logic": "MUST_MATCH_ANY",
        "rules": [
            {"field": "Description", "operator": "CONTAINS", "value": "HOME"}
        ],
    }
    transactions = [
        _tx(Description="HOME DEPOT", Debit=10.0),
        _tx(Description="COFFEE SHOP", Debit=5.0),
    ]

    report = evaluate_rule(rule, transactions, expected_matches=[0])

    assert report["matches"] == [transactions[0]]
    assert report["false_positives"] == []
    assert report["false_negatives"] == []


def test_group_and_between_with_all_logic():
    rule = {
        "logic": "MUST_MATCH_ALL",
        "rules": [
            {
                "group_logic": "MUST_MATCH_ANY",
                "rules": [
                    {"field": "Description", "operator": "CONTAINS", "value": "ESSO"},
                    {"field": "Description", "operator": "CONTAINS", "value": "7-ELEVEN"},
                ],
            },
            {"field": "Debit", "operator": "BETWEEN", "value": [20.0, 120.0]},
        ],
    }

    transactions = [
        _tx(Description="ESSO CIRCLE K", Debit=50.0),
        _tx(Description="ESSO CIRCLE K", Debit=10.0),
    ]

    report = evaluate_rule(rule, transactions, expected_matches=[0])

    assert report["matches"] == [transactions[0]]
    assert report["false_positives"] == []
    assert report["false_negatives"] == []


def test_less_than_or_equal_operator():
    rule = {
        "logic": "MUST_MATCH_ANY",
        "rules": [
            {"field": "Debit", "operator": "LESS_THAN_OR_EQUAL_TO", "value": 50.0}
        ],
    }

    transactions = [
        _tx(Description="SMALL", Debit=40.0),
        _tx(Description="LARGE", Debit=60.0),
    ]

    report = evaluate_rule(rule, transactions, expected_matches=[0])

    assert report["matches"] == [transactions[0]]
    assert report["false_positives"] == []
    assert report["false_negatives"] == []


def test_invalid_operator_yields_no_match():
    rule = {
        "logic": "MUST_MATCH_ANY",
        "rules": [
            {"field": "Description", "operator": "BAD_OPERATOR", "value": "X"}
        ],
    }

    transactions = [_tx(Description="X", Debit=1.0)]
    report = evaluate_rule(rule, transactions)

    assert report["matches"] == []
    assert report["false_positives"] == []
    assert report["false_negatives"] == []


def test_missing_field_returns_no_match():
    rule = {
        "logic": "MUST_MATCH_ANY",
        "rules": [
            {"field": "Balance", "operator": "LESS_THAN_OR_EQUAL_TO", "value": 0.0}
        ],
    }
    transactions = [_tx()]  # Balance is None in base

    report = evaluate_rule(rule, transactions, expected_matches=[])

    assert report["matches"] == []
    assert report["false_positives"] == []
    assert report["false_negatives"] == []


def test_empty_rules_produces_false_negative_when_expected():
    rule = {"logic": "MUST_MATCH_ANY", "rules": []}
    transactions = [_tx(Description="ANY", Debit=1.0)]

    report = evaluate_rule(rule, transactions, expected_matches=[0])

    assert report["matches"] == []
    assert report["false_positives"] == []
    assert report["false_negatives"] == [transactions[0]]


def test_false_positive_detection():
    rule = {
        "logic": "MUST_MATCH_ANY",
        "rules": [
            {"field": "Description", "operator": "CONTAINS", "value": "COFFEE"}
        ],
    }
    transactions = [
        _tx(Description="COFFEE SHOP", Debit=5.0),
        _tx(Description="COFFEE BEANS", Debit=15.0),
    ]

    report = evaluate_rule(rule, transactions, expected_matches=[0])

    assert report["matches"] == transactions
    assert report["false_positives"] == [transactions[1]]
    assert report["false_negatives"] == []
