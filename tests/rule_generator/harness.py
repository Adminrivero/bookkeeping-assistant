"""Reusable test harness helpers for the Rule Generator Wizard."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.rule_generator import (
    evaluate_rule,
    load_rules,
    save_rules,
    validate_rule_block,
    validate_rules_document as _validate_rules_document,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TRANSACTIONS_PATH = FIXTURES_DIR / "transactions.json"
VALID_RULES_PATH = FIXTURES_DIR / "rules_valid.json"
INVALID_RULES_PATH = FIXTURES_DIR / "rules_invalid.json"
EDGE_RULES_PATH = FIXTURES_DIR / "rules_edge_cases.json"


def load_canonical_transactions() -> List[Dict[str, Any]]:
    return json.loads(TRANSACTIONS_PATH.read_text(encoding="utf-8"))


def load_valid_rules() -> List[Dict[str, Any]]:
    return json.loads(VALID_RULES_PATH.read_text(encoding="utf-8"))


def load_invalid_rules() -> List[Dict[str, Any]]:
    return json.loads(INVALID_RULES_PATH.read_text(encoding="utf-8"))


def load_edge_case_rules() -> List[Dict[str, Any]]:
    return json.loads(EDGE_RULES_PATH.read_text(encoding="utf-8"))


def run_evaluation(
    rule: Dict[str, Any],
    transactions: Iterable[Dict[str, Any]],
    *,
    expected_matches: Optional[Iterable[int]] = None,
):
    return evaluate_rule(rule, transactions, expected_matches=expected_matches)


def validate_rule(rule: Dict[str, Any]):
    return validate_rule_block(rule)


def validate_rules_document(doc: Dict[str, Any]):
    return _validate_rules_document(doc)


def round_trip_rules(rules_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Save then load rules via the adapter to ensure structure is preserved."""

    with tempfile.TemporaryDirectory() as tmpdir:
        rules_path = Path(tmpdir) / "rules.json"
        save_rules(rules_dict, path=rules_path)
        reloaded = load_rules(rules_path)
    return reloaded
