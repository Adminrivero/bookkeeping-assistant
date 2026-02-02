## 🧩 Module Breakdown

**Overview**
- Small bookkeeping assistant that ingests statements (CSV and PDF), classifies transactions using rule files, and exports summarized spreadsheets.
- Command-line entrypoint is `project.py` which wires together `ingest` → `classify` → `export` flows.

`project.py`
- Application entry point; implements `main()`.
- Parses CLI flags (year, rules file, `--log`, `--no-progress`).
- Toggles global behaviour (e.g., enable logging via `src.utils.use_logging`).
- Calls appropriate ingest, classify, and export functions.

**Config**
- `config/allocation_rules.json`
  - Stores classification rules (merchant keywords, thresholds, categories). Validated by the rule schema.
- `config/bank_profiles/`
  - Per-bank profile JSON files (e.g., `triangle.json`).
  - Profiles describe how to recognize and parse sections in PDF statements (match text, column indexes, header labels, table_settings).
- `config/schemas/`
  - `bank_profile_schema.json` — canonical JSON Schema that enforces required fields, types and allowed values for bank profile entries (e.g., `match_text`, `header_labels`, `column_indexes`, `table_settings`, `vertical_strategy`, `date_format`, `amount_format`).
  - Profile schema is used at load-time (via `src.utils.load_bank_profile`) to validate bank profile JSON files, emit helpful validation errors, and ensure parsing code and tests/CI can rely on a consistent profile structure.
  - `rule_schema.json` — canonical/legacy-compatible JSON Schema for allocation rules (used by the Rule Generator and validator).
  - Rule schema files are validated at test time and are loaded via `src/rule_generator.schema` helpers.

**Source modules (high level)**
- `src/rule_generator/`
  - Schema loader/validator helpers (load_rule_schema, validate_instance)
  - Future place for adapters/migration and rule-generation helpers
  - Tests live under `tests/rule_generator/`

- `src/ingest.py`
  - Reads and normalizes CSV statements.
  - Cleans column names, parses dates, standardizes formats.
  - Returns normalized transaction dicts suitable for classification.

- `src/pdf_ingest.py`
  - PDF statement parsing for credit card statements; uses bank profiles validated against `bank_profile_schema.json`.
  - Discovers PDFs, normalizes filenames, extracts tables, and normalizes transactions using bank profiles.

- `src/classify.py`
  - Core rule engine applying allocation rules; relies on canonical rule schema & tests.
  - `TransactionClassifier` applies allocation rules from `allocation_rules.json`.
  - Marks ambiguous entries for manual review and emits structured classification results.

- `src/export.py`
  - Builds final spreadsheet using `openpyxl`.
  - Adds formulas, summary sheets, and formatting.
  - Exports CSV/XLSX outputs to `output/<year>/`.

- `src/utils.py`
  - Has the unified `notify()` for printing/logging, path helpers, loaders, and validation helpers.
  - Shared helpers and `normalize_tx_to_canonical_shape` to produce the canonical transaction shape.

**Pipeline behavior**
- `project.main()` collects ingested transactions from multiple files and sorts them chronologically before classification/export to ensure deterministic ordering.
- `run_pipeline(... tax_year=...)` accepts/propagates tax_year (prefers CLI arg; falls back to inference from transactions) and calls exporter.set_tax_year prior to building headers.

**Tests**
- `tests/`
  - Unit tests cover ingest, classification rules, export formatting, and utility helpers.
- `tests/rule_generator/`
  - Contains Rule/schema tests and validate `config/schemas/rule_schema.json` against `config/allocation_rules.json` and example legacy rules.

**Developer notes**
- Logging vs notify: prefer `src.utils.notify()` to keep output consistent across CLI and programmatic runs.
- Debugging: 
  - Visual crops and search strips are saved to `.pydebug/`.
  - Enable via `VSCODE_DEBUGGING=1` or by attaching a debugger.
- Bank profile validation: `load_bank_profile` validates profiles against `bank_profile_schema.json`.
- PDF parsing: supports `table_settings` (from `pdfplumber`), `header_labels`, and `footer_row_text` for precise extraction.

**Quickstart**
- Ingest + classify + export for 2024 with logging:
  - `python project.py --year 2024 --rules config/allocation_rules.json --log`
- Run PDF parsing in debug mode (env var):
  - `VSCODE_DEBUGGING=1 python project.py --year 2024 --rules config/allocation_rules.json`
- Programmatic debug:
  - call `ingest_year("2024", "triangle", debug=True)`
- Run tests:
  - `pytest tests/`
  - `pytest tests/ -q`
  - `pytest tests/rule_generator -q`  # run rule/schema tests only

**Notes**
- Add tests for new parsing heuristics and keep bank_profiles tuned against sample statements.
