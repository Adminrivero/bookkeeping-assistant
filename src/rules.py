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

    def load(self) -> list:
        """Load rules from JSON file and validate schema."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Rules file not found: {self.path}")

        with open(self.path, "r") as f:
            data = json.load(f)

        if "_rules" not in data or not isinstance(data["_rules"], list):
            raise ValueError("Invalid ruleset: missing '_rules' array")

        self.rules = data["_rules"]
        return self.rules

    def get_rules(self) -> list:
        """Return loaded rules."""
        if not self.rules:
            raise RuntimeError("Rules not loaded. Call load() first.")
        return self.rules