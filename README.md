# 🧾 Bookkeeping Assistant

![Run Unit Tests](https://github.com/Adminrivero/Bookkeeping-Assistant/actions/workflows/tests.yml/badge.svg)

#### Video Demo: [Watch on YouTube](https://youtu.be/1lb6IjtB24M)

---

## 📖 Overview

Bookkeeping Assistant is a modular Python tool designed to automate the classification of financial transactions for small business bookkeeping.  
It streamlines the yearly chore of organizing transactions from bank accounts and credit card statements into a structured spreadsheet using rule-based logic.

Originally built as a CS50P final project, the system has evolved into a flexible, extensible assistant for real-world bookkeeping automation.

---

## 🎯 Features

- Ingests CSV, Excel, and PDF statements with automatic column mapping and support for multiple bank formats
- Applies JSON-driven classification rules with nested groups, multiple operators, and per-rule confidence scoring
- Flags ambiguous transactions for manual review (CSV export with suggested matches and metadata)
- Supports per-transaction allocation splits and user-customizable categories via `allocation_rules.json`
- Generates a formatted Excel spreadsheet with formulas and summaries
- Organizes outputs into year-based directories under `output/` and creates tax-ready summaries
- CLI with options for year, rules file, logging, progress bar, dry-run and export skipping (`--year`, `--rules`, `--log`, `--no-progress`, `--dry-run`)
- Optional progress bar and improved logging terminal output for Windows (`tqdm`, `logging`)
- Multi-bank support with profile configs (Triangle, CIBC, TD Visa)
- Dual ingestion paths: PDF parsing or direct CSV validation
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
├── project.py &nbsp;&nbsp;&nbsp; # Main entry point with main() and core functions<br>
├── config/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── allocation_rules.json &nbsp;&nbsp;&nbsp; # Classification rules<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── profile_template.json &nbsp;&nbsp;&nbsp; # JSON schema for validation <br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── bank_profiles/ &nbsp;&nbsp;&nbsp; # Bank profile configs (Triangle, CIBC, TD Visa) <br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── triangle.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── cibc.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── td_visa.json<br>
├── data/ &nbsp;&nbsp;&nbsp; # Input files<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── 2025/ &nbsp;&nbsp;&nbsp; # Tax year with transaction files<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── account.csv &nbsp;&nbsp;&nbsp; # Bank account activity/transactions (`.csv`)<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── triangle/ &nbsp;&nbsp;&nbsp; # Credit card statements from Triangle MasterCard (`.pdf`)<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; │ &nbsp;&nbsp;&nbsp;&nbsp; ├── triangle_jan.pdf<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; │ &nbsp;&nbsp;&nbsp;&nbsp; └── triangle_feb.pdf<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── td_visa/ &nbsp;&nbsp;&nbsp; # Statements from TD Visa (`.pdf` or `.csv`)<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── td_visa_mar.pdf<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── td_visa_apr.csv<br>
├── output/<br> 
│ &nbsp;&nbsp;&nbsp;&nbsp; └── 2025/bookkeeping_2025.xlsx<br> 
├── src/ &nbsp;&nbsp;&nbsp; # Modular components<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── \_\_init\_\_.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── export.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── mapping.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── pipeline.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── rules.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── pdf_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── spreadsheet_schema.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── utils.py<br>
├── tests/ &nbsp;&nbsp; # Unit tests<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_pdf_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_pipeline.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_project.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_project_smoke.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── test_rules_integration.py<br>
└── docs/ &nbsp;&nbsp;&nbsp; # Extended documentation<br>

---

## 🚀 Getting Started

To get the Bookkeeping Assistant running, you must first define your transaction classification rules.

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Adminrivero/bookkeeping-assistant.git
   cd bookkeeping-assistant
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Define Classification Rules (Crucial Step)**: The assistant requires a set of rules to categorize and allocate transactions.

   - **In v2.0**: Use the dedicated **Rule Generator Wizard** (`rulegen.py`) to guide you through creating your classification rules and saving them to `./config/allocation_rules.json`.

   - *(Alternatively, you can manually create or edit the `./config/allocation_rules.json` file if you are familiar with the schema.)*

4. **Place Input Files**: Place your bank and credit card **CSV/PDF files** into the appropriate directories within `data/{year}/`.

5. **Run the Assistant**:

   ```bash
   python project.py --year 2025
   ```

6. **View Output**: View the generated spreadsheet in `output/{year}/`.

---

## 🖥️ CLI Usage

Run the assistant from the command line:

```bash
python project.py --year 2025
```

### Options

- `--year <YEAR>` or `-y <YEAR>` -> Target financial year (default: current year)

- `--bank <BANK_ID...>` or `-b <BANK_ID...>` -> One or more bank/institution IDs. This enables credit card statement ingestion.

- `--rules <PATH>` or `-r <PATH>` -> Path to JSON allocation rules (default: `config/allocation_rules.json`)

- `--log` or `-l` -> Enable logging output

- `--no-progress` or `-q` -> Disable progress bar

### Examples:

1. **Default Bank Account Ingestion** (CSVs only, from `./data/2024/` root input directory)

    ```bash
    python project.py --year 2024 --log
    ```

2. **Ingestion with Credit Card Statements** (Auto-detects files (PDF or CSV) under `./data/2025/triangle/` and `./data/2025/cibc/` subdirectories)

    ```bash
    python project.py --year 2025 --bank triangle cibc
    ```

3. **Indicating Specific Allocation Rules** (Processing 2024 data using a custom ruleset and enabling detailed logging)

    ```bash
    python project.py --year 2024 --rules config/allocation_rules_2024.json --log
    ```

---

## 🧪 Run Tests

```bash
pytest -v
```

---

## 📚 Documentation

For detailed guides, see the docs:

- [**Allocation Ruleset Schema**](./docs/allocation_ruleset_schema.md) - Reference guide for defining the JSON-driven classification rules
- **Rules Creation Assistant** – Guide for defining classification rules
- [**PDF Ingestion**](./docs/pdf_ingestion.md) – How to place PDFs in `data/{year}/bank/` and run CLI
- [**Bank Profiles**](./docs/bank_profiles.md) – How to add new bank configs
- [**Config Schema**](./docs/config_schema.md) – JSON schema validation rules
- [**Module Breakdown**](./docs/module_breakdown.md) - Describe each core module and its role in the pipeline
- [**Testing**](./docs/testing.md) – How to run and extend pytest fixtures
- [**Contributing**](./docs/contributing.md) – Workflow, branches, commit hygiene

---

## 📌 Notes

- Classification rules can be updated in `config/allocation_rules.json`.
- Ambiguous transactions will be flagged for manual review in the Notes column.
- Logging can be enabled with `--log` or `-l` for detailed transparency.
