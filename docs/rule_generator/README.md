# Rule Generator Wizard (RGW) v2.0

The Rule Generator Wizard streamlines authoring legacy-compatible allocation rules for the bookkeeping-assistant. It provides:
- An interactive CLI wizard (`rulegen.py`) for creating and validating rules.
- A deterministic core state machine (`RuleWizard`) that builds schema-valid rule blocks.
- Validation and evaluation helpers to keep rules aligned with the legacy DSL.
- A shared test harness with canonical fixtures for repeatable testing.

## Architecture at a Glance
- **CLI Layer**: `rulegen.py` orchestrates prompts, validation, dry-run evaluation, and saving rules. Business logic stays in lower layers.
- **Core**: `src/rule_generator/core.py` (`RuleWizard`) assembles rule blocks, integrates validation and optional dry-run evaluation.
- **Evaluation**: `src/rule_generator/rule_evaluator.py` executes the legacy DSL (logic, groups, operators) over canonical transactions.
- **Validation**: `src/rule_generator/schema.py` validates rules/documents against `config/schemas/rule_schema.json`.
- **I/O**: `src/rule_generator/rules_io.py` handles safe load/save with optional validation.
- **Test Harness**: `tests/rule_generator/harness.py` plus fixtures provide canonical data for tests.

## Quickstart
1. Activate your virtualenv and install deps: `pip install -r requirements.txt`.
2. Run the interactive wizard: `python rulegen.py --hints` (adds contextual tips).
3. Validate existing rules: `python rulegen.py --validate`.
4. Dry-run all rules against transactions: `python rulegen.py --dry-run --transactions path/to/tx.json`.
5. Explore docs:
   - [usage_guide.md](usage_guide.md)
   - [cli_walkthrough.md](cli_walkthrough.md)
   - [developer_notes.md](developer_notes.md)
   - Constraints/contracts: see `docs/rule_generator/rule_generator_constraints.md`, `rule_evaluation_contract.md`, `test_harness_contract.md`.

## Rule Schema Expectations
Rules must conform to `config/schemas/rule_schema.json` (legacy DSL) with logic/grouping, supported operators, and optional metadata (`rule_id`, `priority`, `scope`). Dual-entry bookkeeping is optional except where required by the transaction type.

## Validation & Dry-Run
- **Schema validation**: `validate_rule_block()` and `validate_rules_document()` ensure structure correctness.
- **Evaluation**: `evaluate_rule()` tests matching against canonical transactions; CLI exposes this via dry-run prompts.

## Testing
Use the harness utilities and fixtures:
- Canonical transactions: `tests/rule_generator/fixtures/transactions.json`.
- Valid/invalid/edge rules: `tests/rule_generator/fixtures/`.
- Helpers: `tests/rule_generator/harness.py`.

Stay within the constraints defined in `rule_generator_constraints.md`; the schema is authoritative.
