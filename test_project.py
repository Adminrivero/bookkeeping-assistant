import os
import json
import pytest
from project import validate_environment, load_rules, run_pipeline

def test_validate_environment(tmp_path):
    # Setup dummy files
    year = 2025
    checking = tmp_path / f"checking_activity_{year}.csv"
    credit = tmp_path / f"credit_card_1_{year}.csv"
    checking.write_text("date,description,amount\n")
    credit.write_text("date,description,amount\n")

    # Patch os.path.exists to look in tmp_path
    original_exists = os.path.exists
    os.path.exists = lambda path: path in [str(checking), str(credit)]

    assert validate_environment(year) is True

    os.path.exists = original_exists  # Restore

def test_load_rules(tmp_path):
    rules_file = tmp_path / "test_rules.json"
    rules_file.write_text(json.dumps({"office_expense": ["Staples"]}))
    rules = load_rules(str(rules_file))
    assert "office_expense" in rules
    assert "Staples" in rules["office_expense"]

def test_run_pipeline(monkeypatch):
    # To be implemented based on actual pipeline functions
    pass