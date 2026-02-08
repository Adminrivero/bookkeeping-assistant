"""Deterministic evaluator for legacy rule DSL."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

MatchReport = Dict[str, List[Dict[str, Any]]]


def _normalize_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _op_contains(field_value: Any, expected: Any) -> bool:
    if field_value is None or expected is None:
        return False
    return expected.lower() in field_value.lower()


def _op_starts_with(field_value: Any, expected: Any) -> bool:
    if field_value is None or expected is None:
        return False
    return field_value.lower().startswith(expected.lower())


def _op_equals(field_value: Any, expected: Any) -> bool:
    if field_value is None and expected is None:
        return True
    if field_value is None or expected is None:
        return False
    return _normalize_string(field_value).lower() == _normalize_string(expected).lower()


def _op_between(field_value: Any, expected: Any) -> bool:
    try:
        low, high = expected
        return float(low) <= float(field_value) <= float(high)
    except Exception:
        return False


def _op_lte(field_value: Any, expected: Any) -> bool:
    try:
        return float(field_value) <= float(expected)
    except Exception:
        return False


_OPERATOR_DISPATCH = {
    "CONTAINS": _op_contains,
    "STARTS_WITH": _op_starts_with,
    "EQUALS": _op_equals,
    "BETWEEN": _op_between,
    "LESS_THAN_OR_EQUAL_TO": _op_lte,
}


def _evaluate_condition(condition: Dict[str, Any], transaction: Dict[str, Any]) -> bool:
    operator = condition.get("operator")
    if operator not in _OPERATOR_DISPATCH:
        return False

    field_name = condition.get("field")
    field_value = transaction.get(field_name)
    expected_value = condition.get("value")

    return _OPERATOR_DISPATCH[operator](field_value, expected_value)


def _evaluate_rule_items(items: List[Dict[str, Any]], transaction: Dict[str, Any], logic: str) -> bool:
    results: List[bool] = []
    for item in items:
        if "group_logic" in item:
            group_logic = item.get("group_logic", "MUST_MATCH_ANY")
            group_rules = item.get("rules", [])
            if not isinstance(group_rules, list) or not group_rules:
                results.append(False)
                continue
            group_result = _evaluate_rule_items(group_rules, transaction, group_logic)
            results.append(group_result)
        else:
            results.append(_evaluate_condition(item, transaction))

    if not results:
        return False

    if logic == "MUST_MATCH_ALL":
        return all(results)
    return any(results)


def evaluate_rule(
    rule: Dict[str, Any],
    transactions: Iterable[Dict[str, Any]],
    *,
    expected_matches: Optional[Iterable[int]] = None,
) -> MatchReport:
    """Apply a single rule block to transactions and produce a match report."""

    logic = rule.get("logic", "MUST_MATCH_ANY")
    items = rule.get("rules", [])

    matches: List[Dict[str, Any]] = []
    matched_indexes: List[int] = []

    for idx, tx in enumerate(transactions):
        if _evaluate_rule_items(items, tx, logic):
            matches.append(tx)
            matched_indexes.append(idx)

    expected = set(expected_matches or [])
    matched = set(matched_indexes)

    false_positives: List[Dict[str, Any]] = []
    false_negatives: List[Dict[str, Any]] = []

    if expected:
        for idx, tx in enumerate(transactions):
            if idx in matched and idx not in expected:
                false_positives.append(tx)
            if idx in expected and idx not in matched:
                false_negatives.append(tx)

    return {
        "matches": matches,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }
