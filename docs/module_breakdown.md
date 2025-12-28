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
  - Profiles describe how to recognize and parse sections in PDF statements (match text, column indexes, header labels, table_settings).

`src/ingest.py`
- Reads and normalizes CSV statements.
- Cleans column names, parses dates, standardizes formats.
- Returns normalized transaction dicts suitable for classification.

`src/pdf_ingest.py`
- PDF statement parsing for credit card statements.
- Discovers PDFs, normalizes filenames, extracts tables, and normalizes transactions using bank profiles.
- Header validation and structural checks (via `validate_table_structure`) are used to identify transaction tables robustly.
- Table edge detection helpers:
  - `get_header_bbox`, `get_label_edge`, `get_table_edges` help compute crop areas and explicit vertical lines.
  - `get_table_edges()` can return explicit vertical lines which are injected into `table_settings["explicit_vertical_lines"]` when `vertical_strategy` == `"explicit"`.
- Debugging:
  - `debug_parse_pdf()` provides detailed extraction, visual debug artifacts, and printouts to fine-tune heuristics.
  - Debug mode can be enabled three ways:
    - Pass `debug=True` to `parse_pdf()` or `ingest_year()`.
    - Set environment var `VSCODE_DEBUGGING=1` (auto-detected).
    - Attach a debugger (auto-detected via `sys.gettrace()`).
  - There is also a legacy `debug_parse_pdf_deprecated()` retained for reference.
- Uses `src.utils.notify()` for consistent messaging (console vs logging).

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
- Logging vs notify: prefer `src.utils.notify()` to keep output consistent across CLI and programmatic runs.
- Debugging: to quickly enter debug mode for PDF parsing:
  - Export `VSCODE_DEBUGGING=1` and run the tool (auto-detected).
  - Or attach your debugger (tools that set `sys.gettrace()` will auto-enable debug).
  - Programmatically call `ingest_year(year, bank, debug=True)` to force debug parsing.
- Bank profile validation: `load_bank_profile` validates profiles against `profile_template.json` — ensure schemas stay in sync.
- PDF parsing: profiles map `match_text`, `header_labels`, and per-section `columns` (indexes). Adjust `table_settings` (tolerances, vertical_strategy) and `header_labels` if bank statement layout changes.
- When using `vertical_strategy: "explicit"`, `pdf_ingest` may compute and inject `explicit_vertical_lines` to improve column alignment.
- Keep rules and profiles under version control and add tests for any parsing edge-cases discovered in live statements.

Quickstart
- Ingest + classify + export for 2024 with logging:
  - `python project.py --year 2024 --rules config/allocation_rules.json --log`
- Run PDF parsing in debug mode (env var):
  - `VSCODE_DEBUGGING=1 python project.py --year 2024 --rules config/allocation_rules.json`
- Programmatic debug:
  - call `ingest_year("2024", "triangle", debug=True)`
- Run tests:
  - `pytest tests/`

Notes
- Add tests for new parsing heuristics and keep bank_profiles tuned against sample statements.
