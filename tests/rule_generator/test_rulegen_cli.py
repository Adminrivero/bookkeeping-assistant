import json
import pytest
import rulegen
from types import SimpleNamespace
from pathlib import Path


def _write_rules(path: Path, rules: dict) -> None:
    path.write_text(json.dumps(rules), encoding="utf-8")


def test_wizard_creates_and_saves_rule(tmp_path: Path, monkeypatch, capsys):
    rules_path = tmp_path / "rules.json"
    _write_rules(
        rules_path,
        {
            "_name": "rules",
            "_version": "1",
            "_description": "",
            "_scope": [],
            "_rules": [],
        },
    )

    responses = iter(
        [
            "Office Expenses",  # category
            "EXPENSE",  # transaction type
            "",  # rule id default slug
            "",  # scope default
            "MUST_MATCH_ANY",  # logic
            "condition",  # add condition
            "Description",  # field
            "CONTAINS",  # operator
            "HOME DEPOT",  # value
            "finish",  # finish
            "y",  # configure dual entry
            "Office Expenses",  # DR name
            "I",  # DR letter
            "Shareholder",  # CR name
            "F",  # CR letter
            "1.0",  # percentage
            "y",  # validate
            "n",  # dry run
            "y",  # save
        ]
    )

    input_fn = lambda prompt="": next(responses)

    result = rulegen.run_wizard(SimpleNamespace(hints=False, rules_path=rules_path), input_fn=input_fn)
    captured = capsys.readouterr()
    assert "Rule saved" in captured.out

    saved = json.loads(rules_path.read_text(encoding="utf-8"))
    assert len(saved["_rules"]) == 1
    rule = saved["_rules"][0]
    assert rule["rule_id"] == "office-expenses"
    assert rule["logic"] == "MUST_MATCH_ANY"
    assert rule["dual_entry"]["DR_COLUMN"]["name"] == "Office Expenses"
    assert result["validation"]["valid"] is True


def test_hints_show_suggestions(tmp_path: Path, monkeypatch, capsys):
    rules_path = tmp_path / "rules.json"
    _write_rules(
        rules_path,
        {
            "_name": "rules",
            "_version": "1",
            "_description": "",
            "_scope": [],
            "_rules": [
                {
                    "category_name": "Fuel",
                    "transaction_type": "EXPENSE",
                    "logic": "MUST_MATCH_ANY",
                    "rules": [{"field": "Description", "operator": "CONTAINS", "value": "ESSO"}],
                }
            ],
        },
    )

    responses = iter(
        [
            "New Category",
            "EXPENSE",
            "",
            "",
            "MUST_MATCH_ANY",
            "finish",
            "n",
            "y",
            "n",
            "n",
        ]
    )
    input_fn = lambda prompt="": next(responses)

    rulegen.run_wizard(SimpleNamespace(hints=True, rules_path=rules_path), input_fn=input_fn)
    captured = capsys.readouterr()
    assert "Existing categories: Fuel" in captured.out


def test_validation_mode_reports_errors(tmp_path: Path, capsys):
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, {"_rules": []})

    rulegen.main(["--validate", "--rules-path", str(rules_path)])
    captured = capsys.readouterr()
    assert "errors" in captured.out or "Schema validation" in captured.out


def test_dry_run_mode_outputs_matches(tmp_path: Path, capsys):
    rules_path = tmp_path / "rules.json"
    tx_path = tmp_path / "tx.json"

    _write_rules(
        rules_path,
        {
            "_name": "rules",
            "_version": "1",
            "_description": "",
            "_scope": [],
            "_rules": [
                {
                    "category_name": "Coffee",
                    "transaction_type": "EXPENSE",
                    "logic": "MUST_MATCH_ANY",
                    "rules": [{"field": "Description", "operator": "CONTAINS", "value": "COFFEE"}],
                }
            ],
        },
    )
    tx_path.write_text(
        json.dumps(
            [
                {
                    "Date": "2025-01-01",
                    "Description": "COFFEE SHOP",
                    "Debit": 5.0,
                    "Credit": 0.0,
                    "Balance": None,
                    "source": "unit",
                }
            ]
        ),
        encoding="utf-8",
    )

    rulegen.main(["--dry-run", "--transactions", str(tx_path), "--rules-path", str(rules_path)])
    captured = capsys.readouterr()
    assert "Rule #0" in captured.out


def test_between_value_parsing(tmp_path: Path, monkeypatch):
    rules_path = tmp_path / "rules.json"
    _write_rules(
        rules_path,
        {
            "_name": "rules",
            "_version": "1",
            "_description": "",
            "_scope": [],
            "_rules": [],
        },
    )

    responses = iter(
        [
            "Fuel",
            "EXPENSE",
            "",
            "",
            "MUST_MATCH_ALL",
            "condition",
            "Debit",
            "LESS_THAN_OR_EQUAL_TO",
            "50",
            "group",
            "MUST_MATCH_ANY",
            "condition",
            "Description",
            "CONTAINS",
            "ESSO",
            "finish",
            "finish",
            "n",
            "y",
            "n",
            "n",
        ]
    )
    input_fn = lambda prompt="": next(responses)

    result = rulegen.run_wizard(SimpleNamespace(hints=False, rules_path=rules_path), input_fn=input_fn)
    rule = result["rule"]
    assert rule["logic"] == "MUST_MATCH_ALL"
    assert rule["rules"][0]["operator"] == "LESS_THAN_OR_EQUAL_TO"
    assert isinstance(rule["rules"][0]["value"], float)
    assert rule["rules"][1]["group_logic"] == "MUST_MATCH_ANY"
