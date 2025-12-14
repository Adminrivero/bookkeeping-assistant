## 🧩 Module Breakdown

Overview
- Small bookkeeping assistant that ingests statements (CSV and PDF), classifies transactions using rule files, and exports summarized spreadsheets.
- Command-line entrypoint is `project.py` which wires together `ingest` → `classify` → `export` flows.

`project.py`
- Application entry point; implements `main()`.
- Parses CLI flags (year, rules file, `--log`, `--no-progress`).
- Toggles global behaviour (e.g., enable logging via `src.utils.use_logging`).
- Calls appropriate ingest, classify, and export functions.

Config
- `config/allocation_rules.json`
  - Stores classification rules (merchant keywords, thresholds, categories).
  - JSON structure validated by rules loader.
- `config/bank_profiles/`
  - Per-bank profile JSON files (e.g., `triangle.json`) plus a `profile_template.json` schema.
  - Profiles describe how to recognize and parse sections in PDF statements.

`src/ingest.py`
- Reads and normalizes CSV statements.
- Cleans column names, parses dates, standardizes formats.
- Returns normalized transaction dicts suitable for classification.

`src/pdf_ingest.py`
- PDF statement parsing for credit card statements.
- Discovers PDFs, normalizes filenames, extracts tables, and normalizes transactions using bank profiles.
- Note: This module should use `src.utils.notify()` for output consistency (see Developer notes).

`src/classify.py`
- Core rule engine.
- `TransactionClassifier` applies allocation rules from `allocation_rules.json`.
- Marks ambiguous entries for manual review and emits structured classification results.

`src/export.py`
- Builds final spreadsheet using `openpyxl`.
- Adds formulas, summary sheets, and formatting.
- Exports CSV/XLSX outputs to `output/<year>/`.

`src/utils.py`
- Helper functions: unified `notify()` for printing/logging, path helpers, loaders, and validation helpers.
- `notify(message, level="info")` centralizes console vs logging behaviour (controlled by `use_logging`).

`tests/`
- Unit tests cover ingest, classification rules, export formatting, and utility helpers.
- Uses pytest; run with `pytest tests/`.

Developer notes
- Logging vs notify: prefer `src.utils.notify()` (prints or uses python logging when `use_logging` is enabled) to keep output consistent across CLI and programmatic runs.
- Bank profile validation: `load_bank_profile` validates profiles against `profile_template.json` — ensure schemas stay in sync.
- PDF parsing: profiles map `match_text` and per-section `columns` (indexes) — adjust profiles if bank statement layout changes.
- CSV ingest: expected top-level CSVs in `data/<year>/`; missing files raise helpful errors via utils functions.

Quickstart
- Ingest + classify + export for 2024 with logging:
  - `python project.py --year 2024 --rules config/allocation_rules.json --log`
- Run tests:
  - `pytest tests/`

Notes
- Keep rules and profiles under version control when updating classification logic or adding banks.
- Add tests for any parsing edge-cases discovered in live statements.