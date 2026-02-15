# CLI Walkthrough (Interactive Wizard Flow)

The wizard follows a fixed sequence. Hints/examples appear only when `--hints` is passed. Dynamic discovery uses existing rules to suggest categories and DR/CR columns.

## Step 1 — Intent
1. Category name (suggestions shown when hints are on).
2. Transaction type (choices): EXPENSE, INCOME_TO_OFFSET_EXPENSE, MANUAL_CR, MANUAL_DR, IGNORE_TRANSACTION.
3. Rule ID (defaults to slugified category name; hints explain slugging).
4. Scope (comma-separated; blank defaults to the standard scope list).
5. Logic: MUST_MATCH_ANY (OR) or MUST_MATCH_ALL (AND); hints clarify semantics.

## Step 2 — Build Conditions & Groups
Prompt: “Add a condition, add a group, or finish?”
- **Condition**: choose field (e.g., Description, Debit, Credit, Balance, Date); choose operator (CONTAINS, STARTS_WITH, EQUALS, BETWEEN, LESS_THAN_OR_EQUAL_TO); enter value (BETWEEN accepts `[min, max]`, numeric operators parse floats).
- **Group**: choose group_logic (MUST_MATCH_ANY/ALL), then add conditions inside the group sub-loop.

## Step 3 — Dual-Entry Bookkeeping
Skipped for IGNORE_TRANSACTION. Otherwise:
- Ask to configure dual-entry (y/n).
- Collect DR/CR column names and letters (NONE/blank => null). Hints show discovered names/letters from existing rules.
- Collect percentage (defaults to 1.0).

## Step 4 — Validation
Prompt to run schema validation via `validate_rule_block()`. Print success or structured errors (path + message).

## Step 5 — Dry-Run Evaluation
Prompt to run `evaluate_rule()` against a user-supplied transactions JSON and optional expected match indexes. Output match/false-positive/false-negative counts.

## Step 6 — Save
Prompt to save to `allocation_rules.json` (or `--rules-path`). Uses the rules I/O adapter for atomic, formatting-stable writes.

## Hints / Examples System
- Enabled with `--hints`.
- Provides category suggestions, DR/CR name/letter suggestions, operator lists, and slugification note.

## Dynamic Discovery
Existing rules are read to populate suggestions for categories and dual-entry columns. No schema or logic is inferred—only strings are surfaced for user convenience.

## Modes Summary
- Interactive wizard: default when no mode flags are used.
- Validation mode: `--validate`.
- Dry-run mode: `--dry-run --transactions <path>`.
- Advanced mode: `--advanced-mode` (reserved; no extra behavior yet).
