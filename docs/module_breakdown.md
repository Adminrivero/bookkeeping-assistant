## 🧩 Module Breakdown

`project.py`
- Application entry point, contains `main()` function
- Uses `argparse` to specify year, rules file, and options (`--log`, `--no-progress`).

`config/allocation_rules.json`
- Stores classification rules (merchant keywords, thresholds, categories)
- Easy to update without touching code

`src/ingest.py`
- Reads and normalizes CSV files
- Cleans column names, parses dates, standardizes formats

`src/classify.py`
- Core rule engine
- Uses OOP: `TransactionClassifier` class
- Applies rules from `allocation_rules.json` to each transaction
- Flags ambiguous entries for manual review

`src/export.py`
- Builds final spreadsheet using `openpyxl`
- Adds formulas, summary sheets, formatting

`src/utils.py`
- Helper functions: unified `notify()` for print/logging, reusable utilities.

`tests/`
- Unit tests for each module using `pytest`