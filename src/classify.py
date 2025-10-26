import re

# Operator functions
OPERATORS = {
    "CONTAINS": lambda s, v: v.lower() in (s or "").lower(),
    "STARTS_WITH": lambda s, v: (s or "").lower().startswith(v.lower()),
    "EQUALS": lambda a, v: str(a).lower() == str(v).lower(),
    "REGEX": lambda s, pattern: re.search(pattern, s or "") is not None,
    "GREATER_THAN": lambda n, v: float(n) > float(v),
    "GREATER_THAN_OR_EQUAL_TO": lambda n, v: float(n) >= float(v),
    "LESS_THAN": lambda n, v: float(n) < float(v),
    "LESS_THAN_OR_EQUAL_TO": lambda n, v: float(n) <= float(v),
    "BETWEEN": lambda n, rng: float(rng[0]) <= float(n) <= float(rng[1]),
}

class TransactionClassifier:
    """
    Applies allocation_rules.json to classify transactions.
    Evaluates rules in priority order until a match is found.
    """

    def __init__(self, rules: list):
        self.rules = rules

    def classify(self, transaction: dict) -> dict:
        """
        Classify a single transaction.
        Returns a dict with category, transaction_type, and dual_entry mapping.
        """
        for rule in self.rules:
            if self._evaluate_rule(rule, transaction):
                return {
                    "category": rule["category_name"],
                    "transaction_type": rule["transaction_type"],
                    "dual_entry": rule.get("dual_entry"),
                }
        # Default: manual review
        return {
            "category": "Unclassified",
            "transaction_type": "MANUAL_CR" if transaction.get("Debit") else "MANUAL_DR",
            "dual_entry": None,
        }

    def _evaluate_rule(self, rule: dict, transaction: dict) -> bool:
        """Evaluate a rule against a transaction."""
        logic = rule.get("logic", "MUST_MATCH_ANY")
        conditions = rule.get("rules", [])

        results = []
        for cond in conditions:
            if "group_logic" in cond:  # Nested group
                group_results = [
                    self._apply_operator(sub, transaction) for sub in cond["rules"]
                ]
                results.append(
                    all(group_results) if cond["group_logic"] == "MUST_MATCH_ALL" else any(group_results)
                )
            else:
                results.append(self._apply_operator(cond, transaction))

        return all(results) if logic == "MUST_MATCH_ALL" else any(results)

    def _apply_operator(self, cond: dict, transaction: dict) -> bool:
        """Apply a single operator to a transaction field."""
        field = cond["field"]
        operator = cond["operator"]
        value = cond["value"]
        field_value = transaction.get(field)

        func = OPERATORS.get(operator)
        if not func:
            raise ValueError(f"Unsupported operator: {operator}")

        try:
            return func(field_value, value)
        except Exception:
            return False