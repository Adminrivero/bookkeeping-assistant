# 🧾 Bookkeeping Assistant

#### Video Demo: [URL HERE]()

#### Description:

A modular Python tool designed to automate the classification and export of financial transactions for small business bookkeeping. Built as the final project for CS50's Introduction to Programming with Python, this assistant streamlines the yearly chore of organizing bank and credit card statements into a structured spreadsheet using rule-based logic.

## 🎯 Features

- Ingests CSV/Excel files from checking accounts and credit cards
- Applies classification rules to categorize transactions (e.g., office vs vehicle expenses)
- Flags ambiguous entries for manual review
- Generates a formatted Excel spreadsheet with formulas and summaries
- Organizes output files into year-based directories

## 🧠 Technologies

- Python 3
- `pandas` for data processing
- `openpyxl` or `xlsxwriter` for spreadsheet generation
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
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── raw/ &nbsp;&nbsp; # Input files (checking, credit cards)<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── processed/ &nbsp;&nbsp; # Cleaned and categorized files<br>
├── output/<br> 
│ &nbsp;&nbsp;&nbsp;&nbsp; └── bookkeeping_2025.xlsx<br> 
├── src/ &nbsp;&nbsp; # Modular components<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── export.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── utils.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── models.py<br>
├── tests/ &nbsp;&nbsp; # Unit tests<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_project.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── test_export.py<br>

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

`src/models.py`
- Defines `Transaction` dataclass
- Optional: `Account`, `Statement`, or `ClassificationResult` classes

`tests/`
- Unit tests for each module
- Use `unittest` or `pytest`


## ✅ CS50P Requirements

- Contains a `main()` function inside `project.py`
- Includes at least three additional functions with corresponding `pytest` tests
- Contains a `test_project.py` with the test functions for those additional functions within `project.py`
- Contains a requirements.txt with the pip-installable libraries required by the project
- Demonstrates modular design, OOP, error handling, and CLI usage

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


