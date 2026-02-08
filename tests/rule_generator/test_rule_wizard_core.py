from src.rule_generator.core import RuleWizard


BASE_TX = {
    "Date": "2025-01-01",
    "Description": "",
    "Debit": 0.0,
    "Credit": 0.0,
    "Balance": None,
    "source": "unit",
}


def _tx(**override):
    tx = dict(BASE_TX)
    tx.update(override)
    return tx


def test_simple_flow_builds_valid_rule_and_dry_run():
    wizard = RuleWizard()
    wizard.set_intent(category_name="Office", transaction_type="EXPENSE", logic="MUST_MATCH_ANY")
    wizard.add_condition("Description", "CONTAINS", "HOME DEPOT")
    wizard.set_dual_entry(dr_name="Office Expenses", dr_letter="I", cr_name="Shareholder", cr_letter="F")

    transactions = [_tx(Description="HOME DEPOT", Debit=20.0), _tx(Description="OTHER", Debit=5.0)]
    result = wizard.finalize_rule(validate=True, dry_run_transactions=transactions, expected_matches=[0])

    assert result["validation"] is not None
    assert result["validation"]["valid"] is True

    match_report = result["match_report"]
    assert match_report is not None
    assert match_report["matches"] == [transactions[0]]
    assert match_report["false_positives"] == []
    assert match_report["false_negatives"] == []

    rule = result["rule"]
    assert rule["category_name"] == "Office"
    assert rule["transaction_type"] == "EXPENSE"
    assert rule["logic"] == "MUST_MATCH_ANY"
    assert "dual_entry" in rule


def test_nested_group_all_logic():
    wizard = RuleWizard(root_logic="MUST_MATCH_ALL")
    wizard.set_intent(category_name="Fuel", transaction_type="EXPENSE")
    wizard.add_group(
        "MUST_MATCH_ANY",
        [
            {"field": "Description", "operator": "CONTAINS", "value": "ESSO"},
            {"field": "Description", "operator": "CONTAINS", "value": "7-ELEVEN"},
        ],
    )
    wizard.add_condition("Debit", "BETWEEN", [20.0, 120.0])

    transactions = [_tx(Description="ESSO CIRCLE K", Debit=50.0), _tx(Description="ESSO", Debit=10.0)]
    result = wizard.finalize_rule(validate=True, dry_run_transactions=transactions, expected_matches=[0])

    assert result["validation"] is not None
    assert result["validation"]["valid"] is True
    
    match_report = result["match_report"]
    assert match_report is not None
    assert match_report["matches"] == [transactions[0]]
    assert match_report["false_positives"] == []
    assert match_report["false_negatives"] == []

    rule = result["rule"]
    assert rule["rules"][0]["group_logic"] == "MUST_MATCH_ANY"


def test_invalid_rule_fails_validation():
    wizard = RuleWizard()
    wizard.set_intent(category_name="Bad", transaction_type="EXPENSE")
    wizard.add_condition("Description", "BAD_OPERATOR", "X")

    result = wizard.finalize_rule(validate=True)
    assert result["validation"] is not None
    assert result["validation"]["valid"] is False
    assert result["match_report"] is None


def test_metadata_is_preserved():
    wizard = RuleWizard()
    wizard.set_intent(
        category_name="Office",
        transaction_type="EXPENSE",
        rule_id="office_rule",
        priority=10,
        scope="td_visa",
    )
    wizard.add_condition("Description", "CONTAINS", "OFFICE")

    result = wizard.finalize_rule(validate=False)
    rule = result["rule"]

    assert rule["rule_id"] == "office_rule"
    assert rule["priority"] == 10
    assert rule["scope"] == "td_visa"


def test_missing_intent_raises():
    wizard = RuleWizard()
    wizard.add_condition("Description", "CONTAINS", "OFFICE")

    try:
        wizard.finalize_rule()
        assert False, "Expected ValueError"
    except ValueError:
        pass
