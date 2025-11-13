## 🛠️ Work Layout Toward v1.0 (CS50P Capstone)

### 📌 Phase 1: Foundation & Compliance

- **Branch:** `config/project-setup`

- **Tasks:**

  - Create `project.py` with `main()` and at least 3 additional functions (`get_cli_args`, `setup_paths`, `load_rules`). (**Done** ✅)

  - Add `test_project.py` in root with tests for those functions. (**Done** ✅)

  - Ensure repo structure matches CS50P requirements. (**Done** ✅)

### 📌 Phase 2: Schema & Ruleset

- **Branch:** `config/allocation-rules`

- **Tasks:**

  - Finalize `allocation_rules.json`. (**Done** ✅)

  - Document schema in `README.md`. (**Done** ✅)

  - Add validation logic in `RuleLoader`. (**Done** ✅)

### 📌 Phase 3: Rule Engine Core

- **Branch:** `feature/rule-engine-core`

- **Tasks:**

  - Implement `RuleLoader` (loads and validates JSON). (**Done** ✅)

  - Implement `TransactionClassifier` (evaluates rules, applies dual-entry). (**Done** ✅)

  - Add operator functions (`CONTAINS`, `BETWEEN`, etc.). (**Done** ✅)

  - Unit tests for operator evaluation and rule matching. (**Done** ✅)

  - Add integration test to validate the real `allocation_rules.json` against sample transactions. (**Done** ✅)

### 📌 Phase 4: Ingestion & Export

- **Branch:** `feature/io-pipeline`

- **Tasks:**

  - Add schema module (`spreadsheet_schema.py`) to centralize column definitions. (**Done** ✅)

  - Implement `export.py` (generate spreadsheet with schema, formulas, formatting). (**Done** ✅)

  - Add transaction-to-schema mapping function (`mapping.py`) to connect the classifier output to the exporter. (**Done** ✅)

  - Implement the pipeline module (runner) for workflow orchestration (ingest $\rightarrow$ classify $\rightarrow$ map $\rightarrow$ export). (**Done** ✅)

  - Implement `ingest.py` (read CSV/Excel, normalize). (**Done** ✅)

### 📌 Phase 5: Integration & CLI

- **Branch:** `feature/cli-integration`

- **Tasks:**

  - Wire ingestion → classification → export in `run_pipeline`. (**Done** ✅)

  - Add CLI options (`--year`, `--no-progress`, etc.). (**Done** ✅)

  - Implement progress bar for `run_pipeline` steps (e.g., using `tqdm` or similar library). (**Done** ✅)

  - Add logging for transparency. (**Done** ✅)

### 📌 Phase 6: Testing & Documentation

- **Branch:** `tests/full-suite`

- **Tasks:**

  - Expand `tests/` with unit and integration tests. (**Done** ✅)

  - Ensure at least 3 functions in ./`project.py` are tested with pytest, and implemented in ./`test_project.py`. (**Done** ✅)

  - Document usage in `README.md` (installation, running, testing). (**Done** ✅)

### Phase 7: Final Polish & Submission

- **Branch:** `release/v1.0`

- **Tasks:**

  - Clean up repo (remove debug prints, finalize README) (**Done** ✅)

  - Tag release `v1.0`. (**Done** ✅)

  - Prepare submission package for CS50P. (**Done** ✅)

## 🧭 v2.0 Work Layout (Roadmap for Tax Year 2025)

### 📌 Phase 1: PDF Ingestion (High Priority)

- **Goal:** Accept bank and credit card statements in PDF format.

- **Branch:** `feature/pdf-ingestion`

- **Tasks:**

  - Design src/pdf_ingest.py to extract tabular data using pdfplumber or PyMuPDF

  - Create bank_profiles/ directory with JSON configs for each institution (column mappings, header rules)

  - Refactor ingestion pipeline to support both CSV and PDF inputs

  - Add CLI flag --pdf or auto-detect .pdf files in data/{year}/

  - Write unit tests for PDF parsing and normalization

  - Update README with PDF support instructions

### 📌 Phase 2: Rule Generator Assistant (High Priority)

- **Goal:** Provide a guided CLI wizard that hides JSON and dual-entry complexity, enabling non-technical users to generate valid `allocation_rules.json` files.

- **Branch:** `feature/rule-generator`

- **Tasks:**

  1. **Chart of Accounts Config**
     - Create `config/chart_of_accounts.json` mapping human-friendly category names to DR/CR columns.
     - Load this config in the wizard to abstract column letters from the user.

  2. **Wizard Flow Implementation**
     - Step 1: Prompt for transaction type (EXPENSE, INCOME, IGNORE).
     - Step 2: Prompt for category selection from chart of accounts.
     - Step 3: Prompt for keywords/vendors and logic choice (ANY vs ALL).
     - Step 4: Optional refinement logic (amount filters, BETWEEN operator).
     - Step 5: Review & confirm human-readable summary before saving.

  3. **Validation & Error Handling**
     - Validate numeric inputs (amounts, menu choices).
     - Normalize and deduplicate keywords.
     - Prevent duplicate rules by checking existing JSON before saving.
     - Ensure schema compliance before writing to file.

  4. **Advanced User Mode**
     - Add option for manual DR/CR column definition.
     - Support custom operators (e.g., STARTS_WITH, MATCHES_REGEX).

  5. **Batch Mode (Optional for v2.0)**
     - Allow importing a CSV of vendor/category pairs to auto-generate multiple rules.
     - CLI flag: `--import vendors.csv`.

  6. **Testing & Validation**
     - Write unit tests for wizard prompts and JSON output.
     - Add `--validate` flag to check schema compliance of existing `allocation_rules.json`.
     - Add dry-run mode to preview generated JSON without saving.

  7. **Documentation**
     - Update README with usage examples:
       ```bash
       python rulegen.py
       ```
     - Provide sample chart_of_accounts.json and example generated rules.
     - Document advanced mode and batch mode usage.
