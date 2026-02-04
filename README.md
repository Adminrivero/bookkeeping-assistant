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

### 📥 Ingestion & Normalization
- **Multi-Format Support**: Seamlessly parses **CSV**, **Excel**, and **PDF** bank statements.
- **Bank Profiles**: Extensible JSON configuration system allows defining custom mappings, header detection, and parsing rules for any institution (e.g., Triangle, CIBC, TD Visa).
- **Dual-Path Processing**: Supports both direct CSV validation and PDF text extraction with automatic column mapping.

### 🧠 Intelligent Classification
- **Advanced Logic Engine**: JSON-driven ruleset utilizing nested `AND`/`OR` groups and a wide range of operators (`CONTAINS`, `STARTS_WITH`, `BETWEEN`, `REGEX`).
- **Precision Bookkeeping**: Supports transaction splitting (allocating one expense to multiple categories) and specific Credit/Debit column mapping via a `chart_of_accounts`.
- **Ambiguity Detection**: Automatically flags low-confidence matches or unclassified transactions for manual review in the verification export.

### 🧙‍♂️ Rule Generator Wizard (v2.0 Preview)
- **Interactive CLI**: A guided terminal assistant (`rulegen.py`) to create and validate categorization rules without manual JSON editing.
- **Validation & Safety**:
  - **Schema Compliance**: Real-time validation against `rule_schema.json` to prevent syntax errors.
  - **Match Reports**: "Dry-run" capability to test rules against canonical transaction data, reporting matches, false positives, and false negatives.
  - **Safe I/O**: Modifies `allocation_rules.json` while preserving existing formatting and comments.
- **Advanced Mode**: Power-user interface for defining complex operators and custom dual-entry logic strings.

### 📊 Export & Reporting
- **Tax-Ready Output**: Generates formatted `.xlsx` workbooks with built-in formulas, categorization summaries, and visual formatting.
- **Project Organization**: Automatically structures input and output files into year-based directories (`data/2025/`, `output/2025/`).

### ⚙️ Developer Experience
- **Robust CLI**: Comprehensive command-line arguments for year selection, logging verbosity (`--log`), progress bars (`tqdm`), and "dry-run" pipeline execution.
- **Testing Standard**: High-coverage unit and integration test suite via `pytest` and GitHub Actions CI.

---

## 🧠 Technologies

- **Core**: Python 3 (Type Hinting, OOP, Modular Design)
- **Data & Validation**:
  - `jsonschema` – Strict validation for rule definitions (`rule_schema.json`) and bank profiles
  - `openpyxl` – Excel spreadsheet generation, formulas, and formatting
- **CLI & UX**:
  - `argparse` – Command-line interface handling
  - `tqdm` – Progress bar visualization
  - `colorama` – Cross-platform terminal coloring
  - `logging` – Structured diagnostic output
- **PDF Processing**:
  - `pdfplumber` & `pdfminer.six` – Text extraction and table parsing
  - `pypdfium2` & `Pillow` – Rendering and image processing
- **Quality Assurance**:
  - `pytest` – Unit and integration testing framework

---

## 📁 Project Structure
bookkeeping-assistant/<br>
├── README.md<br>
├── requirements.txt<br>
├── project.py &nbsp;&nbsp;&nbsp; # Main entry point (Analysis & Report pipeline)<br>
├── rulegen.py &nbsp;&nbsp;&nbsp; # Rule Generator Wizard (CLI)<br>
├── config/<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── allocation_rules.json &nbsp;&nbsp;&nbsp; # Active classification rules<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── bank_profiles/ &nbsp;&nbsp;&nbsp; # Bank profile configs (Triangle, CIBC, TD Visa)<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; │ &nbsp;&nbsp;&nbsp;&nbsp; ├── triangle.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; │ &nbsp;&nbsp;&nbsp;&nbsp; ├── cibc.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; │ &nbsp;&nbsp;&nbsp;&nbsp; └── td_visa.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── schemas/ &nbsp;&nbsp;&nbsp; # JSON Schemas for validation<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── bank_profile_schema.json<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── rule_schema.json<br>
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
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── classify.py &nbsp;&nbsp;&nbsp; # Rule matching engine<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── csv_ingest.py &nbsp; # CSV parsing specific logic<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── export.py &nbsp;&nbsp;&nbsp;&nbsp; # Excel generation & summary formulas<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── ingest.py &nbsp;&nbsp;&nbsp;&nbsp; # General statement normalization<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── mapping.py &nbsp;&nbsp;&nbsp; # Account/Category mapping<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── pdf_ingest.py &nbsp; # PDF extraction using bank profiles<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── pipeline.py &nbsp;&nbsp; # Process orchestration<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── rules.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; # Rule loading & schema validation helpers<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── spreadsheet_schema.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── utils.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; # Shared helpers & notify system<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── rule_generator/ &nbsp;&nbsp;&nbsp; # Wizard internal logic<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── schema.py<br>
├── tests/ &nbsp;&nbsp; # Unit & Integration tests<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_classify.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_export_summary.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_pdf_ingest.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_pipeline_integration.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_project.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; ├── test_utils.py<br>
│ &nbsp;&nbsp;&nbsp;&nbsp; └── rule_generator/ &nbsp;&nbsp;&nbsp; # Wizard-specific test suite<br>
│ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── test_rule_schema_validation.py<br>
└── docs/ &nbsp;&nbsp;&nbsp; # Extended documentation<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── rule_generator/ &nbsp;&nbsp;&nbsp; # Wizard design & evaluation contracts<br>

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
