# Usage Guide

This guide explains how to run the Rule Generator Wizard CLI, its flags, and common workflows.

## Running the CLI
```
python rulegen.py [FLAGS]
```

### Flags
- `--hints` — show contextual tips (examples, field/operator reminders, slug note).
- `--dry-run` — evaluate all existing rules against a transactions file (requires `--transactions`).
- `--transactions <path>` — path to JSON array of canonical transactions for dry-run.
- `--validate` — validate the entire `allocation_rules.json` against the schema.
- `--advanced-mode` — reserved; enables future advanced options (no extra logic today).
- `--rules-path <path>` — override rules file location (default `config/allocation_rules.json`).

## Example Commands
- Interactive wizard with hints: `python rulegen.py --hints`
- Validate rules file: `python rulegen.py --validate`
- Dry-run all rules: `python rulegen.py --dry-run --transactions data/2025/2025_td_accountactivity_100_sample.json`
- Dry-run using a custom rules file: `python rulegen.py --dry-run --transactions tx.json --rules-path tmp/rules.json`

## Example Rule Creation Session (interactive)
1. Start: `python rulegen.py --hints`
2. Provide category name, transaction type, optional rule_id (defaults to slug), scope (comma list or blank for default), and logic (ANY/ALL).
3. Add conditions or groups (operator-specific parsing: BETWEEN as `[min,max]`, numeric for `LESS_THAN_OR_EQUAL_TO`).
4. Configure dual-entry if applicable (DR/CR names/letters, percentage; `NONE`/blank yields null columns).
5. Choose to validate (schema check) and optionally dry-run against a transaction file.
6. Save to `allocation_rules.json` (or overridden `--rules-path`).

## Example Dry-Run Session
```
python rulegen.py --dry-run --transactions tests/rule_generator/fixtures/transactions.json
```
Outputs per rule: rule index, category name, and match count.

## Example Validation Session
```
python rulegen.py --validate
```
Prints schema validation success or lists structured errors (path + message).

## Notes
- Scope input accepts comma-separated values; stored as a comma-joined string.
- Rule IDs default to slugified category names.
- Only legacy DSL operators are supported: CONTAINS, STARTS_WITH, EQUALS, BETWEEN, LESS_THAN_OR_EQUAL_TO.
- Transactions must follow the canonical shape from `test_harness_contract.md`.
