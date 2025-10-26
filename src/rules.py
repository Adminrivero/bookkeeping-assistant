import json
import os

class RuleLoader:
    """
    Loads and validates allocation_rules.json.
    Provides access to the ordered list of rules.
    """

    def __init__(self, path: str):
        self.path = path
        self.rules = []
    
    def _validate_rule(self, rule: dict):
        """Validate a single rule object against schema requirements."""
        required_fields = ["category_name", "transaction_type", "logic", "rules"]
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Rule missing required field: {field}")

        if rule["transaction_type"] != "IGNORE_TRANSACTION":
            if "dual_entry" not in rule:
                raise ValueError(f"Rule {rule['category_name']} requires dual_entry")

        # Validate operators
        for cond in rule.get("rules", []):
            if "group_logic" in cond:  # Nested group
                if "rules" not in cond or not isinstance(cond["rules"], list):
                    raise ValueError(f"Invalid group in rule {rule['category_name']}")
                for sub in cond["rules"]:
                    self._validate_condition(sub, rule["category_name"])
            else:
                self._validate_condition(cond, rule["category_name"])
    
    def _validate_condition(self, cond: dict, category: str):
        """Validate a single condition object."""
        if "field" not in cond or "operator" not in cond or "value" not in cond:
            raise ValueError(f"Condition missing fields in rule {category}")
        
        if cond["operator"] not in [
            "CONTAINS", "STARTS_WITH", "EQUALS", "REGEX",
            "GREATER_THAN", "GREATER_THAN_OR_EQUAL_TO",
            "LESS_THAN", "LESS_THAN_OR_EQUAL_TO", "BETWEEN"
        ]:
            raise ValueError(f"Unsupported operator {cond['operator']} in rule {category}")

    def load(self) -> list:
        """Load rules from JSON file and validate schema."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Rules file not found: {self.path}")

        with open(self.path, "r") as f:
            data = json.load(f)

        if "_rules" not in data or not isinstance(data["_rules"], list):
            raise ValueError("Invalid ruleset: missing '_rules' array")

        self.rules = data["_rules"]
        
        # Validate each rule
        for rule in self.rules:
            self._validate_rule(rule)
            
        return self.rules

    def get_rules(self) -> list:
        """Return loaded rules."""
        if not self.rules:
            raise RuntimeError("Rules not loaded. Call load() first.")
        return self.rules