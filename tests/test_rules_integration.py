import pytest
import os
import json
from src.rules import RuleLoader
from src.classify import TransactionClassifier

@pytest.fixture(scope="module")
def ruleset():
    """Load the real allocation_rules.json file."""
    path = os.path.join("config", "allocation_rules.json")
    loader = RuleLoader(path)
    return loader.load()

@pytest.fixture
def classifier(ruleset):
    """Instantiate classifier with real ruleset."""
    return TransactionClassifier(ruleset)

# --------------------------
# Integration Tests
# --------------------------

def test_vehicle_insurance_rule(classifier):
    tx = {"Description": "Economical Insurance Premium", "Debit": 200.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Vehicle Expenses - Insurance & Services"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "L"
    assert result["dual_entry"]["CR_COLUMN"]["letter"] == "F"

def test_fido_bill_rule(classifier):
    tx = {"Description": "FIDO Mobile Bill", "Debit": 75.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Telephone - Fido Bill"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "N"

def test_bank_fee_rule(classifier):
    tx = {"Description": "MONTHLY ACCOUNT FEE", "Debit": 15.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Bank Fees - Monthly Account Fee"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "P"

def test_bank_rebate_rule(classifier):
    tx = {"Description": "ACCT BAL REBATE", "Debit": "", "Credit": 5.00}
    result = classifier.classify(tx)
    assert result["category"] == "Bank Fees - Account Rebate"
    assert result["dual_entry"]["APPLY_PERCENTAGE"] == 1.0

def test_vehicle_fuel_range_rule(classifier):
    tx = {"Description": "ESSO CIRCLE K", "Debit": 50.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Vehicle Expenses - Fuel (Range Based)"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "L"

def test_business_coffee_rule(classifier):
    tx = {"Description": "TIM HORTONS #123", "Debit": 4.50, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Food/Drink Expenses - Business Meal or Coffee"
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "T"

def test_client_gifts_rule(classifier):
    tx = {"Description": "LCBO Purchase", "Debit": 60.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Client Gifts - Wine/Spirits/Restaurant/Gift Cards/Baked Goods/Etc."
    assert result["dual_entry"]["DR_COLUMN"]["letter"] == "V"

def test_ignore_internal_transfer(classifier):
    tx = {"Description": "TRIANGLE MC PAYMENT", "Debit": 500.00, "Credit": ""}
    result = classifier.classify(tx)
    assert result["transaction_type"] == "IGNORE_TRANSACTION"

def test_unclassified_fallback(classifier):
    tx = {"Description": "UNKNOWN MERCHANT", "Debit": 123.45, "Credit": ""}
    result = classifier.classify(tx)
    assert result["category"] == "Unclassified"
    assert result["dual_entry"] is None
