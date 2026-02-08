"""Non-interactive rule wizard core state machine."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, TypedDict

from .rule_evaluator import evaluate_rule, MatchReport
from .schema import ValidationResult, validate_rule_block


class RuleBuildResult(TypedDict):
    rule: Dict[str, Any]
    validation: Optional[ValidationResult]
    match_report: Optional[MatchReport]


class RuleWizard:
    """Deterministic builder for legacy rule blocks."""

    def __init__(
        self,
        *,
        root_logic: str = "MUST_MATCH_ANY",
        validator=validate_rule_block,
        evaluator=evaluate_rule,
    ) -> None:
        self._root_logic = root_logic
        self._validator = validator
        self._evaluator = evaluator

        self._category_name: Optional[str] = None
        self._transaction_type: Optional[str] = None
        self._rule_id: Optional[str] = None
        self._priority: Optional[int] = None
        self._scope: Optional[str] = None
        self._dual_entry: Optional[Dict[str, Any]] = None
        self._rules: List[Dict[str, Any]] = []

    def set_intent(
        self,
        *,
        category_name: str,
        transaction_type: str,
        rule_id: Optional[str] = None,
        priority: Optional[int] = None,
        scope: Optional[str] = None,
        logic: Optional[str] = None,
    ) -> None:
        self._category_name = category_name
        self._transaction_type = transaction_type
        self._rule_id = rule_id
        self._priority = priority
        self._scope = scope
        if logic is not None:
            self._root_logic = logic

    def add_condition(self, field: str, operator: str, value: Any) -> None:
        self._rules.append({"field": field, "operator": operator, "value": value})

    def add_group(self, group_logic: str, conditions: List[Dict[str, Any]]) -> None:
        self._rules.append({"group_logic": group_logic, "rules": list(conditions)})

    def set_dual_entry(
        self,
        *,
        dr_name: Optional[str] = None,
        dr_letter: Optional[str] = None,
        cr_name: Optional[str] = None,
        cr_letter: Optional[str] = None,
        apply_percentage: Optional[float] = 1.0,
    ) -> None:
        def _column(name: Optional[str], letter: Optional[str]) -> Optional[Dict[str, Optional[str]]]:
            if name is None and letter is None:
                return None
            return {"name": name, "letter": letter}

        self._dual_entry = {
            "DR_COLUMN": _column(dr_name, dr_letter),
            "CR_COLUMN": _column(cr_name, cr_letter),
            "APPLY_PERCENTAGE": apply_percentage,
        }

    def _build_rule_dict(self) -> Dict[str, Any]:
        if self._category_name is None or self._transaction_type is None:
            raise ValueError("Intent not set")

        rule: Dict[str, Any] = {
            "category_name": self._category_name,
            "transaction_type": self._transaction_type,
            "logic": self._root_logic,
            "rules": list(self._rules),
        }

        if self._rule_id is not None:
            rule["rule_id"] = self._rule_id
        if self._priority is not None:
            rule["priority"] = self._priority
        if self._scope is not None:
            rule["scope"] = self._scope
        if self._dual_entry is not None:
            rule["dual_entry"] = self._dual_entry

        return rule

    def finalize_rule(
        self,
        *,
        validate: bool = True,
        dry_run_transactions: Optional[Iterable[Dict[str, Any]]] = None,
        expected_matches: Optional[Iterable[int]] = None,
    ) -> RuleBuildResult:
        rule = self._build_rule_dict()

        validation: Optional[ValidationResult] = None
        if validate:
            validation = self._validator(rule)

        match_report: Optional[MatchReport] = None
        if dry_run_transactions is not None and (validation is None or validation["valid"]):
            match_report = self._evaluator(
                rule,
                list(dry_run_transactions),
                expected_matches=expected_matches,
            )

        return {
            "rule": rule,
            "validation": validation,
            "match_report": match_report,
        }
