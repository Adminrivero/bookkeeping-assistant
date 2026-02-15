# Developer Notes

This guide explains how the Rule Generator Wizard pieces fit together and how to extend them safely.

## Core Components
- **RuleWizard** (`src/rule_generator/core.py`): deterministic builder for legacy rule blocks; wires optional schema validation and dry-run evaluation. No I/O or prompts.
- **Evaluator** (`src/rule_generator/rule_evaluator.py`): executes legacy DSL (logic + nested groups + operators CONTAINS/STARTS_WITH/EQUALS/BETWEEN/LESS_THAN_OR_EQUAL_TO).
- **Validator** (`src/rule_generator/schema.py`): JSON Schema validation against `config/schemas/rule_schema.json` with structured errors.
- **I/O Adapter** (`src/rule_generator/rules_io.py`): safe load/save with atomic writes; optional validation gate.
- **CLI** (`rulegen.py`): thin orchestration over the above; handles prompts, parsing, and delegation.
- **Harness** (`tests/rule_generator/harness.py`): canonical fixtures + helper APIs for evaluation, validation, and I/O round-trips.

## How the CLI Integrates
- Uses `RuleWizard` to assemble rule data; no business logic lives in the CLI.
- Uses `validate_rule_block()` for schema checks and `evaluate_rule()` for dry-runs.
- Saves via `save_rules()` to avoid formatting drift; loads suggestions via `load_rules()` for dynamic discovery.

## Adding New Operators
1. Add operator implementation to `rule_evaluator.py` dispatch.
2. Update schema (if allowed) and constraints (requires human approval per constraints doc).
3. Extend CLI prompting to list the new operator.
4. Add tests in the harness and CLI layers.

## Extending the Schema
- Schema is authoritative and controlled. Any change requires updating `config/schemas/rule_schema.json`, constraints docs, and corresponding validators/tests. Do not change schema without approval.

## Adding New CLI Modes
- Extend argparse in `rulegen.py` and delegate to dedicated handlers (similar to `--dry-run` / `--validate`). Keep logic thin; reuse core/evaluator/I-O modules.

## Writing Tests with the Harness
- Use fixtures in `tests/rule_generator/fixtures/` for transactions and rules.
- Use helpers from `tests/rule_generator/harness.py`:
  - `load_canonical_transactions()`, `load_valid_rules()`, `load_invalid_rules()`, `load_edge_case_rules()`.
  - `run_evaluation()`, `validate_rule()`, `validate_rules_document()`, `round_trip_rules()`.
- Integration example: see `tests/rule_generator/test_harness_integration.py`.

## Maintaining Fixtures
- Keep fixtures schema-valid (except for intentionally invalid sets) and aligned with canonical transaction shape from `test_harness_contract.md`.
- When adding coverage, expand transactions to represent new edge cases and update tests accordingly.

## Dual-Entry Bookkeeping
- Optional except where required by transaction type; represented with `DR_COLUMN`, `CR_COLUMN`, and `APPLY_PERCENTAGE`.
- CLI supports `NONE`/blank for null columns; Wizard/Core simply stores provided structures.

## Advanced Mode
- `--advanced-mode` is reserved for future extensions; do not embed business logic until requirements are defined.

## Staying Within Constraints
Follow `rule_generator_constraints.md` and `rule_evaluation_contract.md`: deterministic behavior, no schema drift, no hidden overrides, and no business logic in the wizard UI layer.
