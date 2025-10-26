import pytest
from src.classify import TransactionClassifier, OPERATORS

# --------------------------
# Operator Function Tests
# --------------------------

def test_contains_operator():
    assert OPERATORS["CONTAINS"]("Payment to TIM HORTONS", "tim hortons")
    assert not OPERATORS["CONTAINS"]("Payment to STARBUCKS", "tim hortons")

def test_starts_with_operator():
    assert OPERATORS["STARTS_WITH"]("FIDO Mobile Bill", "FIDO")
    assert not OPERATORS["STARTS_WITH"]("Bell Canada", "FIDO")

def test_equals_operator():
    assert OPERATORS["EQUALS"]("MONTHLY ACCOUNT FEE", "monthly account fee")
    assert not OPERATORS["EQUALS"]("ACCT BAL REBATE", "MONTHLY ACCOUNT FEE")

def test_between_operator():
    assert OPERATORS["BETWEEN"](50, [20.01, 120.00])
    assert not OPERATORS["BETWEEN"](10, [20.01, 120.00])

def test_less_than_or_equal_operator():
    assert OPERATORS["LESS_THAN_OR_EQUAL_TO"](5.99, 6.00)
    assert not OPERATORS["LESS_THAN_OR_EQUAL_TO"](7.00, 6.00)

# --------------------------
# Rule Evaluation Tests
# --------------------------

@pytest.fixture
def sample_rules():
    return [
        {
            "category_name": "Business Coffee",
            "transaction_type": "EXPENSE",
            "logic": "MUST_MATCH_ALL",
            "rules": [
                {"field": "Description", "operator": "CONTAINS", "value": "TIM HORTONS"},
                {"field": "Debit", "operator": "LESS_THAN_OR_EQUAL_TO", "value": 6.00}
            ],
            "dual_entry": {
                "DR_COLUMN": {"name": "Food Expenses from Business Meetings", "letter": "T"},
                "CR_COLUMN": {"name": "Shareholder Contribution (CR)", "letter": "F"},
                "APPLY_PERCENTAGE": 1.0
            }
        },
        {
            "category_name": "Vehicle Fuel",
            "transaction_type": "EXPENSE",
            "logic": "MUST_MATCH_ALL",
            "rules": [
                {
                    "group_logic": "MUST_MATCH_ANY",
                    "rules": [
                        {"field": "Description", "operator": "CONTAINS", "value": "ESSO"},
                        {"field": "Description", "operator": "CONTAINS", "value": "7-ELEVEN"}
                    ]
                },
                {"field": "Debit", "operator": "BETWEEN", "value": [20.0, 120.0]}
            ],
            "dual_entry": {
                "DR_COLUMN": {"name": "Vehicle Expenses", "letter": "L"},
                "CR_COLUMN": {"name": "Shareholder Contribution (CR)", "letter": "F"},
                "APPLY_PERCENTAGE": 1.0
            }
        }
    ]

def test_classify_coffee_transaction(sample_rules):
    classifier = TransactionClassifier(sample_rules)
    tx = {"Description": "TIM HORTONS #123", "Debit": 4.50, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Business Coffee"
    assert result["transaction_type"] == "EXPENSE"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "T"

def test_classify_vehicle_transaction(sample_rules):
    classifier = TransactionClassifier(sample_rules)
    tx = {"Description": "ESSO CIRCLE K", "Debit": 50.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Vehicle Fuel"
    assert result["transaction_type"] == "EXPENSE"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "L"

def test_unclassified_transaction(sample_rules):
    classifier = TransactionClassifier(sample_rules)
    tx = {"Description": "UNKNOWN MERCHANT", "Debit": 200.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Unclassified"
    assert result["transaction_type"] in ["MANUAL_CR", "MANUAL_DR"]
    assert result["dual_entry"] is None
