#!/usr/bin/env python3
"""Interactive CLI for the Rule Generator Wizard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.rule_generator import (
    RuleWizard,
    evaluate_rule,
    load_rules,
    save_rules,
    validate_rule_block,
    validate_rules_document,
)

DEFAULT_SCOPE = ["chequing_account", "saving_account", "credit_card"]
VALID_TRANSACTION_TYPES = [
    "EXPENSE",
    "INCOME_TO_OFFSET_EXPENSE",
    "MANUAL_CR",
    "MANUAL_DR",
    "IGNORE_TRANSACTION",
]
VALID_LOGIC = ["MUST_MATCH_ANY", "MUST_MATCH_ALL"]
VALID_OPERATORS = [
    "CONTAINS",
    "STARTS_WITH",
    "EQUALS",
    "BETWEEN",
    "LESS_THAN_OR_EQUAL_TO",
]


def _slugify(text: str) -> str:
    return "-".join(
        part for part in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if part
    )


def _prompt(prompt_text: str, *, input_fn=input, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    return input_fn(f"{prompt_text}{suffix}: ").strip() or (default or "")


def _parse_scope(raw: str) -> List[str]:
    if not raw:
        return list(DEFAULT_SCOPE)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_between(raw: str) -> List[float]:
    cleaned = raw.strip().replace("[", "").replace("]", "")
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    if len(parts) != 2:
        raise ValueError("BETWEEN requires two numeric values")
    return [float(parts[0]), float(parts[1])]


def _parse_value(operator: str, raw: str) -> Any:
    if operator == "BETWEEN":
        return _parse_between(raw)
    if operator == "LESS_THAN_OR_EQUAL_TO":
        return float(raw)
    return raw


def _gather_suggestions(rules_doc: Dict[str, Any]) -> Dict[str, List[str]]:
    categories: List[str] = []
    dr_names: List[str] = []
    cr_names: List[str] = []
    letters: List[str] = []

    for rule in rules_doc.get("_rules", []):
        cat = rule.get("category_name")
        if isinstance(cat, str):
            categories.append(cat)
        dual = rule.get("dual_entry") or {}
        for key in ("DR_COLUMN", "CR_COLUMN"):
            col = dual.get(key) or {}
            name = col.get("name")
            letter = col.get("letter")
            if isinstance(name, str):
                (dr_names if key == "DR_COLUMN" else cr_names).append(name)
            if isinstance(letter, str):
                letters.append(letter)

    return {
        "categories": sorted(set(categories)),
        "dr_names": sorted(set(dr_names)),
        "cr_names": sorted(set(cr_names)),
        "letters": sorted(set(letters)),
    }


def _prompt_condition(*, input_fn=input, print_fn=print, hints: bool) -> Dict[str, Any]:
    if hints:
        print_fn("Fields: Description, Debit, Credit, Balance, Date")
    field = _prompt("Field name", input_fn=input_fn)

    if hints:
        print_fn(f"Operators: {', '.join(VALID_OPERATORS)}")
    operator = _prompt("Operator", input_fn=input_fn).upper()
    while operator not in VALID_OPERATORS:
        print_fn("Invalid operator. Choose one of: " + ", ".join(VALID_OPERATORS))
        operator = _prompt("Operator", input_fn=input_fn).upper()

    value_raw = _prompt("Value", input_fn=input_fn)
    try:
        value = _parse_value(operator, value_raw)
    except ValueError as exc:  # pragma: no cover - defensive
        print_fn(f"Invalid value: {exc}")
        value = value_raw

    return {"field": field, "operator": operator, "value": value}


def _prompt_group(*, input_fn=input, print_fn=print, hints: bool) -> Dict[str, Any]:
    group_logic = _prompt("Group logic (MUST_MATCH_ANY/MUST_MATCH_ALL)", input_fn=input_fn, default="MUST_MATCH_ANY").upper()
    while group_logic not in VALID_LOGIC:
        print_fn("Invalid group logic. Use MUST_MATCH_ANY or MUST_MATCH_ALL")
        group_logic = _prompt("Group logic", input_fn=input_fn).upper()

    group_rules: List[Dict[str, Any]] = []
    while True:
        choice = _prompt("Add condition to group or finish? (condition/finish)", input_fn=input_fn, default="finish").lower()
        if choice == "finish":
            break
        group_rules.append(_prompt_condition(input_fn=input_fn, print_fn=print_fn, hints=hints))

    return {"group_logic": group_logic, "rules": group_rules}


def _prompt_dual_entry(
    *,
    input_fn=input,
    print_fn=print,
    hints: bool,
    suggestions: Dict[str, List[str]],
) -> Dict[str, Any]:
    if hints and suggestions["dr_names"]:
        print_fn("DR suggestions: " + ", ".join(suggestions["dr_names"]))
    dr_name = _prompt("DR_COLUMN name (blank for none)", input_fn=input_fn, default="") or None
    if hints and suggestions["letters"]:
        print_fn("Column letters seen: " + ", ".join(suggestions["letters"]))
    dr_letter = _prompt("DR_COLUMN letter (blank for none)", input_fn=input_fn, default="") or None

    if hints and suggestions["cr_names"]:
        print_fn("CR suggestions: " + ", ".join(suggestions["cr_names"]))
    cr_name = _prompt("CR_COLUMN name (NONE/blank for null)", input_fn=input_fn, default="")
    cr_name = None if not cr_name or cr_name.upper() == "NONE" else cr_name
    cr_letter = _prompt("CR_COLUMN letter (NONE/blank for null)", input_fn=input_fn, default="")
    cr_letter = None if not cr_letter or cr_letter.upper() == "NONE" else cr_letter

    percent_raw = _prompt("Percentage (default 1.0)", input_fn=input_fn, default="1.0")
    try:
        percentage = float(percent_raw)
    except ValueError:
        percentage = 1.0

    def _column(name: Optional[str], letter: Optional[str]) -> Optional[Dict[str, str]]:
        if name is None and letter is None:
            return None
        col: Dict[str, str] = {}
        if name is not None:
            col["name"] = name
        if letter is not None:
            col["letter"] = letter
        return col

    return {
        "DR_COLUMN": _column(dr_name, dr_letter),
        "CR_COLUMN": _column(cr_name, cr_letter),
        "APPLY_PERCENTAGE": percentage,
    }


def run_wizard(args, *, input_fn=input, print_fn=print) -> Dict[str, Any]:
    rules_doc = load_rules(args.rules_path)
    suggestions = _gather_suggestions(rules_doc)

    hints = bool(args.hints)
    if hints and suggestions["categories"]:
        print_fn("Existing categories: " + ", ".join(suggestions["categories"]))

    category_name = _prompt("Category name", input_fn=input_fn)
    if hints:
        print_fn("Tip: use Title Case. Suggestions shown above if available.")
    transaction_type = _prompt(
        "Transaction type (EXPENSE, INCOME_TO_OFFSET_EXPENSE, MANUAL_CR, MANUAL_DR, IGNORE_TRANSACTION)",
        input_fn=input_fn,
    ).upper()
    while transaction_type not in VALID_TRANSACTION_TYPES:
        print_fn("Invalid transaction type. Choose a valid option.")
        transaction_type = _prompt("Transaction type", input_fn=input_fn).upper()

    default_rule_id = _slugify(category_name)
    if hints:
        print_fn(f"Default rule_id slugified: {default_rule_id}")
    rule_id = _prompt("Rule ID", input_fn=input_fn, default=default_rule_id)

    scope_raw = _prompt("Scope (comma separated, blank for default)", input_fn=input_fn, default="")
    scope = _parse_scope(scope_raw)

    if hints:
        print_fn("Logic ANY = OR, ALL = AND")
    logic = _prompt("Logic (MUST_MATCH_ANY/MUST_MATCH_ALL)", input_fn=input_fn, default="MUST_MATCH_ANY").upper()
    while logic not in VALID_LOGIC:
        print_fn("Invalid logic. Use MUST_MATCH_ANY or MUST_MATCH_ALL.")
        logic = _prompt("Logic", input_fn=input_fn).upper()

    scope_value = ",".join(scope) if scope else None

    wizard = RuleWizard(root_logic=logic)
    wizard.set_intent(
        category_name=category_name,
        transaction_type=transaction_type,
        rule_id=rule_id,
        scope=scope_value,
        logic=logic,
    )

    while True:
        choice = _prompt("Add a condition, add a group, or finish? (condition/group/finish)", input_fn=input_fn).lower()
        if choice == "finish":
            break
        if choice == "group":
            group = _prompt_group(input_fn=input_fn, print_fn=print_fn, hints=hints)
            wizard.add_group(group["group_logic"], group["rules"])
        else:
            condition = _prompt_condition(input_fn=input_fn, print_fn=print_fn, hints=hints)
            wizard.add_condition(condition["field"], condition["operator"], condition["value"])

    dual_entry = None
    if transaction_type != "IGNORE_TRANSACTION":
        configure_dual = _prompt("Configure dual-entry bookkeeping? (y/n)", input_fn=input_fn, default="n").lower()
        if configure_dual.startswith("y"):
            dual_entry = _prompt_dual_entry(
                input_fn=input_fn, print_fn=print_fn, hints=hints, suggestions=suggestions
            )
            wizard.set_dual_entry(
                dr_name=(dual_entry.get("DR_COLUMN") or {}).get("name"),
                dr_letter=(dual_entry.get("DR_COLUMN") or {}).get("letter"),
                cr_name=(dual_entry.get("CR_COLUMN") or {}).get("name"),
                cr_letter=(dual_entry.get("CR_COLUMN") or {}).get("letter"),
                apply_percentage=dual_entry.get("APPLY_PERCENTAGE"),
            )

    rule = wizard.finalize_rule(validate=False)["rule"]

    validate_choice = _prompt("Validate rule against schema? (y/n)", input_fn=input_fn, default="y").lower()
    validation_result = None
    if validate_choice.startswith("y"):
        validation_result = validate_rule_block(rule)
        if validation_result["valid"]:
            print_fn("Schema validation: OK")
        else:
            print_fn("Schema validation errors:")
            for issue in validation_result["errors"]:
                print_fn(f" - {issue['path']}: {issue['message']}")

    match_report = None
    dry_run_choice = _prompt("Perform a dry-run evaluation? (y/n)", input_fn=input_fn, default="n").lower()
    if dry_run_choice.startswith("y"):
        tx_path = Path(_prompt("Path to transactions JSON", input_fn=input_fn))
        expected_raw = _prompt("Expected match indexes (comma separated, optional)", input_fn=input_fn, default="")
        expected = [int(x.strip()) for x in expected_raw.split(",") if x.strip()] if expected_raw else []
        transactions = json.loads(tx_path.read_text(encoding="utf-8"))
        match_report = evaluate_rule(rule, transactions, expected_matches=expected)
        print_fn("Dry-run results:")
        print_fn(f" Matches: {len(match_report['matches'])}")
        print_fn(f" False positives: {len(match_report['false_positives'])}")
        print_fn(f" False negatives: {len(match_report['false_negatives'])}")

    save_choice = _prompt("Save this rule to allocation_rules.json? (y/n)", input_fn=input_fn, default="y").lower()
    if save_choice.startswith("y"):
        rules_doc.setdefault("_rules", []).append(rule)
        save_rules(rules_doc, path=args.rules_path)
        print_fn("Rule saved.")

    return {
        "rule": rule,
        "validation": validation_result,
        "match_report": match_report,
    }


def _print_validation(result, print_fn=print):
    if result["valid"]:
        print_fn("Schema validation: OK")
    else:
        print_fn("Schema validation errors:")
        for issue in result["errors"]:
            print_fn(f" - {issue['path']}: {issue['message']}")


def run_validation(args, print_fn=print):
    rules_doc = load_rules(args.rules_path)
    result = validate_rules_document(rules_doc)
    _print_validation(result, print_fn=print_fn)
    return result


def run_dry_run(args, print_fn=print):
    if not args.transactions:
        raise SystemExit("--transactions is required for --dry-run")
    rules_doc = load_rules(args.rules_path)
    transactions = json.loads(Path(args.transactions).read_text(encoding="utf-8"))
    for idx, rule in enumerate(rules_doc.get("_rules", [])):
        report = evaluate_rule(rule, transactions, expected_matches=None)
        print_fn(f"Rule #{idx} {rule.get('category_name')}: matches={len(report['matches'])}")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rule Generator Wizard CLI")
    parser.add_argument("--hints", action="store_true", help="Show hints and examples")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Evaluate rules against transactions")
    parser.add_argument("--transactions", help="Path to transactions JSON for dry-run")
    parser.add_argument("--validate", action="store_true", help="Validate allocation_rules.json")
    parser.add_argument("--advanced-mode", action="store_true", dest="advanced", help="Enable advanced mode (reserved)")
    parser.add_argument("--rules-path", default=Path("config") / "allocation_rules.json", type=Path)
    return parser


def main(argv: Optional[List[str]] = None) -> Any:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        return run_dry_run(args)
    if args.validate:
        return run_validation(args)

    return run_wizard(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
