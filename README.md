# 🧾 Bookkeeping Assistant

#### Video Demo: [URL HERE]()

#### Description:

A modular Python tool designed to automate the classification of financial transactions for small business bookkeeping. Built as a proof-of-concept, this assistant streamlines the yearly chore of organizing transactions from bank accounts and credit card statements into a structured spreadsheet using rule-based logic.

This project involves developing a modular and robust system to manage and automate the allocation of resources based on a set of user-defined rules. The first stable version (v1.0), featuring the initial set of desired features, is specifically suited to meet the requirements for a final project in CS50's Introduction to Programming with Python (CS50P). This system is designed to provide high flexibility and is adaptable to various real-world scenarios. It ensures efficient resource distribution and minimizes manual oversight.

## ✅ CS50P Final Project Requirements

- **Files and Modularity:** The project consists of **at least three `.py` files** (e.g., `project.py`, `classifier.py`, `export.py`), demonstrating strong modular design and separation of concerns.

- **Core Function:** Contains a `main` function within the primary executable file (`project.py`) to initiate the command-line interface (CLI). The `project.py` includes at least three additional custom functions other than `main` with corresponding tests.

- **Testing:** Includes a separate file named **`test_project.py`** that contains **at least three tests** implemented using `pytest`. These tests cover the functionality of the program's core functions.

- **Implementation:** Demonstrates proficiency in **Object-Oriented Programming (OOP)**, robust **error handling**, and effective **command-line usage** (CLI).

- **Dependencies:** Contains a **`requirements.txt`** file listing all necessary pip-installable libraries required for the project to run.

## 🎯 Features

- Ingests CSV/Excel files from checking accounts and credit cards
- Applies classification rules to categorize transactions (e.g., office vs vehicle expenses)
- Flags ambiguous entries for manual review
- Generates a formatted Excel spreadsheet with formulas and summaries
- Organizes output files into year-based directories

## 🧠 Technologies

- Python 3
- `pandas` for data processing
- `openpyxl` for spreadsheet generation
- `argparse` for CLI
- `unittest` and `pytest` for testing

## 📁 Project Structure
bookkeeping-assistant/<br>
├── README.md<br>
├── requirements.txt<br>
├── project.py &nbsp;&nbsp; # Main entry point with main() and core functions<br>
├── config/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── allocation_rules.json &nbsp;&nbsp; # Classification rules<br>
├── data/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── raw/ &nbsp;&nbsp; # Input files (bank transactions `.csv`, credit card statements `.csv`/`.pdf`)<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── processed/ &nbsp;&nbsp; # Cleaned and categorized files<br>
├── output/<br> 
│ &nbsp;&nbsp;&nbsp;&nbsp; └── bookkeeping_2025.xlsx<br> 
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

## 🧩 Module Breakdown

`project.py`
- Application entry point, contains main() function
- Uses `argparse` to specify year, input files, or mode (e.g., dry-run vs export

`config/allocation_rules.json`
- Stores classification rules (merchant keywords, thresholds, categories)
- Easy to update without touching code

`src/ingest.py`
- Reads and normalizes CSV/Excel files
- Cleans column names, parses dates, standardizes formats

`src/classify.py`
- Core rule engine
- Uses OOP: `TransactionClassifier` class
- Applies rules from `allocation_rules.json` to each transaction
- Flags ambiguous entries for manual review

`src/export.py`
- Builds final spreadsheet using `openpyxl` or `xlsxwriter`
- Adds formulas, summary sheets, formatting

`src/utils.py`
- Helper functions: logging, fuzzy matching, regex parsing

`tests/`
- Unit tests for each module
- Use `unittest` or `pytest`

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
2. Place your bank and credit card CSV files in `data/raw/`
3. Run the assistant:
   ```bash
   python project.py --year 2025
   ```
4. View the generated spreadsheet in output/

## 🧪 Run Tests

```bash
pytest tests/
```

## 📌 Notes

- Classification rules can be updated in config/allocation_rules.json
- Ambiguous transactions will be flagged for manual review
- Future enhancements may include fuzzy matching and ML-based classification


