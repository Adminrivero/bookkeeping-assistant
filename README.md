# 🧾 Bookkeeping Assistant

#### Video Demo: [Watch on YouTube](https://youtu.be/1lb6IjtB24M)

---

#### Description:

A modular Python tool designed to automate the classification of financial transactions for small business bookkeeping. Built as a proof-of-concept, this assistant streamlines the yearly chore of organizing transactions from bank accounts and credit card statements into a structured spreadsheet using rule-based logic.

This project involves developing a modular and robust system to manage and automate the allocation of resources based on a set of user-defined rules. The first stable version (v1.0), featuring the initial set of desired features, is specifically suited to meet the requirements for a final project in CS50's Introduction to Programming with Python (CS50P). This system is designed to provide high flexibility and is adaptable to various real-world scenarios. It ensures efficient resource distribution and minimizes manual oversight.

---

## ✅ CS50P Final Project Requirements

- **Files and Modularity:** The project consists of **at least three `.py` files** (e.g., `project.py`, `classifier.py`, `export.py`), demonstrating strong modular design and separation of concerns.

- **Core Function:** Contains a `main` function within the primary executable file (`project.py`) to initiate the command-line interface (CLI). The `project.py` includes at least three additional custom functions other than `main` with corresponding tests.

- **Testing:** Includes a separate file named **`test_project.py`** that contains **at least three tests** implemented using `pytest`. These tests cover the functionality of the program's core functions.

- **Implementation:** Demonstrates proficiency in **Object-Oriented Programming (OOP)**, robust **error handling**, and effective **command-line usage** (CLI).

- **Dependencies:** Contains a **`requirements.txt`** file listing all necessary pip-installable libraries required for the project to run.

---

## 🎯 Features

- Ingests CSV, Excel, and PDF statements with automatic column mapping and support for multiple bank formats
- Applies JSON-driven classification rules with nested groups, multiple operators, and per-rule confidence scoring
- Flags ambiguous transactions for manual review (CSV export with suggested matches and metadata)
- Supports per-transaction allocation splits and user-customizable categories via `allocation_rules.json`
- Exports a formatted Excel workbook (per-account sheets and summary totals), with optional CSV export
- Organizes outputs into year-based directories under `output/` and creates tax-ready summaries
- CLI with options for year, rules file, logging, progress bar, dry-run and export skipping (`--year`, `--rules`, `--log`, `--no-progress`, `--dry-run`, `--skip-export`, `--threshold`)
- Optional progress bar and improved logging/colorized terminal output for Windows (`tqdm`, `logging`, `colorama`)
- Robust unit/integration tests covering ingest, classification, pipeline, and export; CI integration via GitHub Actions

---

## 🧠 Technologies

- **Python 3** – modular, testable codebase using OOP and CLI patterns
- **CLI & UX** – argparse for command-line interface, tqdm for optional progress bar
- **Spreadsheet Export** – openpyxl (with et_xmlfile) for Excel generation, formulas, and formatting
- **Rules Engine** – JSON‑driven classification logic wired through TransactionClassifier and pipeline modules
- **PDF Handling** – pdfminer.six, pdfplumber, pypdfium2, Pillow for parsing and processing statement PDFs
- **Testing** – pytest for unit and integration tests
- **Terminal Experience** – logging for structured logs, colorama for clean Windows output

---

## 📁 Project Structure
bookkeeping-assistant/<br>
├── README.md<br>
├── requirements.txt<br>
├── project.py &nbsp;&nbsp; # Main entry point with main() and core functions<br>
├── config/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── allocation_rules.json &nbsp;&nbsp; # Classification rules<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── bank_profiles/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── triangle.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── cibc.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── td_visa.json<br>
├── data/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── 2025/ &nbsp;&nbsp; # Input files (bank transactions `.csv`)<br>
├── output/<br> 
│ &nbsp;&nbsp;&nbsp;&nbsp; └── 2025/bookkeeping_2025.xlsx<br> 
├── src/ &nbsp;&nbsp; # Modular components<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── \_\_init\_\_.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── export.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── mapping.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── pipeline.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── rules.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── spreadsheet_schema.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── utils.py<br>
├── tests/ &nbsp;&nbsp; # Unit tests<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_project.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_rules_integration.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_export.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── test_pipeline.py<br>

---

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

---

## 📑 JSON Ruleset Schema

The classification engine is driven by an external configuration file: `allocation_rules.json`.  
This file defines an **ordered list of rules** that are evaluated sequentially. The first matching rule is applied, ensuring priority-based classification.

### Rule Object Structure

Each rule has the following fields:

| Field              | Type    | Required | Description |
|--------------------|---------|----------|-------------|
| `category_name`    | String  | ✅ | Human-readable label for the category (e.g., "Office Expenses - Retail/Hardware"). |
| `transaction_type` | String  | ✅ | Defines the accounting action (`EXPENSE`, `INCOME`, `MANUAL_CR`, `MANUAL_DR`, `INCOME_TO_OFFSET_EXPENSE`, `IGNORE_TRANSACTION`). |
| `logic`            | String  | ✅ | Rule evaluation method: `MUST_MATCH_ANY` (OR) or `MUST_MATCH_ALL` (AND). |
| `rules`            | Array   | ✅ | List of conditions or subrules (`field`, `operator`, `value`) or nested groups. |
| `dual_entry`       | Object  | ⚠️ | Required for all except `IGNORE_TRANSACTION`. Defines DR/CR columns and `APPLY_PERCENTAGE`. |

### Condition Fields

- **`field`** → Which transaction field to check (`Description`, `Debit`, `Credit`).  
- **`operator`** → Comparison method (`CONTAINS`, `STARTS_WITH`, `EQUALS`, `BETWEEN`, etc.).  
- **`value`** → String, number, or array depending on operator.  

### Dual Entry Object

```json
"dual_entry": {
  "DR_COLUMN": {"name": "Office Expenses", "letter": "I"},
  "CR_COLUMN": {"name": "Shareholder Contribution (CR)", "letter": "F"},
  "APPLY_PERCENTAGE": 1.0
}
```

- `DR_COLUMN` → Debit side of transaction.
- `CR_COLUMN` → Credit side of transaction.
- `APPLY_PERCENTAGE` → Factor applied to the amount (1.0 = full, 0.66 = partial, -1.0 = rebate).

### Nested Groups

Rules can contain subgroups for complex logic:

```json
{
  "logic": "MUST_MATCH_ALL",
  "rules": [
    {
      "group_logic": "MUST_MATCH_ANY",
      "rules": [
        {"field": "Description", "operator": "CONTAINS", "value": "ESSO"},
        {"field": "Description", "operator": "CONTAINS", "value": "7-ELEVEN"}
      ]
    },
    {"field": "Debit", "operator": "BETWEEN", "value": [20.0, 120.0]}
  ]
}
```

This example matches ("ESSO" **OR** "7-ELEVEN") **AND** any amount between $20.0 - $120.0

## 🚀 Getting Started

1. Clone the repo

   ```bash
   git clone https://github.com/Adminrivero/bookkeeping-assistant.git
   cd bookkeeping-assistant
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Place your bank and credit card CSV files in `data/{year}/`.

4. Run the assistant:
   ```bash
   python project.py --year 2025
   ```
5. View the generated spreadsheet in `output/{year}/`.

---

## 🖥️ Usage

Run the assistant from the command line:

```bash
python project.py --year 2025
```

### Options

- `--year YEAR` or `-y YEAR` <br>
  Target financial year to process. Defaults to the current year.

- `--rules PATH` or `-r PATH` <br>
  Path to the JSON allocation rules file. Defaults to `config/allocation_rules.json`.

- `--log` or `-l` <br>
  Enable logging output (timestamps and levels) instead of simple print statements.

- `--no-progress` or `-q` <br>
  Disable progress bar output for a cleaner CLI experience.

### Example

```bash
python project.py --year 2024 --rules config/allocation_rules.json --log
```

---

## 🧪 Run Tests

```bash
pytest -v
```

## 📌 Notes

- Classification rules can be updated in `config/allocation_rules.json`.
- Ambiguous transactions will be flagged for manual review in the Notes column.
- Logging can be enabled with `--log` or `-l` for detailed transparency.
- Future enhancements may include PDF ingestion, fuzzy matching, and CI integration.
