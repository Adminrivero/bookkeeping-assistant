#!/usr/bin/env python3
"""
Rule Generator Assistant (CLI Wizard)
Guides users through creating classification rules without touching JSON.
"""

import json
import sys
from pathlib import Path
from src.utils import notify

CHART_PATH = Path("config/chart_of_accounts.json")
RULES_PATH = Path("config/allocation_rules.json")


def load_chart_of_accounts():
    with open(CHART_PATH, "r") as f:
        return json.load(f)


def load_existing_rules():
    if RULES_PATH.exists():
        with open(RULES_PATH, "r") as f:
            return json.load(f)
    return {"_rules": []}


def save_rules(rules):
    with open(RULES_PATH, "w") as f:
        json.dump(rules, f, indent=2)
    notify("✨ Rule saved successfully!", level="info")


def wizard():
    chart = load_chart_of_accounts()
    rules = load_existing_rules()

    notify("👋 Welcome to the Bookkeeping Assistant Rule Creator!\n")

    # Step 1: Transaction type
    tx_type = input("Select transaction type [1=EXPENSE, 2=INCOME, 3=IGNORE]: ")
    if tx_type == "1":
        transaction_type = "EXPENSE"
    elif tx_type == "2":
        transaction_type = "INCOME"
    else:
        transaction_type = "IGNORE_TRANSACTION"

    # Step 2: Category selection
    for idx, cat in enumerate(chart["categories"], start=1):
        print(f"[{idx}] {cat['name']}")
    choice = int(input("Enter category number: "))
    category = chart["categories"][choice - 1]

    # Step 3: Keywords
    keywords = input("Enter keywords/vendors (comma separated): ").split(",")
    keywords = [kw.strip() for kw in keywords if kw.strip()]

    logic_choice = input("Should all keywords match? (ALL/ANY): ").upper()
    logic = "MUST_MATCH_ALL" if logic_choice == "ALL" else "MUST_MATCH_ANY"

    # Step 4: Amount filter
    amount_filter = input("Filter by amount? (y/n): ").lower()
    min_amt = None
    max_amt = None
    ruleset = []
    if amount_filter == "y":
        min_amt = float(input("Minimum amount: "))
        max_amt = float(input("Maximum amount: "))
        ruleset = [
            {
                "logic": "MUST_MATCH_ALL",
                "rules": [
                    {"group_logic": logic, "rules": [
                        {"field": "Description", "operator": "CONTAINS", "value": kw}
                        for kw in keywords
                    ]},
                    {"field": "Debit", "operator": "BETWEEN", "value": [min_amt, max_amt]}
                ]
            }
        ]
    else:
        ruleset = [
            {"logic": logic, "rules": [
                {"field": "Description", "operator": "CONTAINS", "value": kw}
                for kw in keywords
            ]}
        ]

    # Step 5: Assemble rule object
    new_rule = {
        "category_name": category["name"],
        "transaction_type": transaction_type,
        "logic": logic,
        "rules": ruleset,
        "dual_entry": category["dual_entry"]
    }

    # Review
    print("\n✅ RULE DRAFT")
    print(f"Category: {category['name']}")
    print(f"Type: {transaction_type}")
    print(f"Triggers: {keywords}")
    if amount_filter == "y":
        print(f"Amount BETWEEN {min_amt} and {max_amt}")
    confirm = input("Save this rule? (y/n): ").lower()
    if confirm == "y":
        rules["_rules"].append(new_rule)
        save_rules(rules)


if __name__ == "__main__":
    wizard()
