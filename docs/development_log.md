## 🛠️ Work Layout Toward v1.0 (CS50P Capstone)

### 📌 Phase 1: Foundation & Compliance

- **Branch:** `config/project-setup`

- **Tasks:**

  - Create `project.py` with `main()` and at least 3 additional functions (`validate_environment`, `load_rules`, `run_pipeline`). (**Done** ✅)

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

  - Add CLI options (`--year`, `--dry-run`, etc.). (**Done** ✅)

  - Implement progress bar for `run_pipeline` steps (e.g., using `tqdm` or similar library). (**Done** ✅)

  - Add logging for transparency.

### 📌 Phase 6: Testing & Documentation

- **Branch:** `tests/full-suite`

- **Tasks:**

  - Expand `tests/` with unit and integration tests.

  - Ensure at least 3 functions in ./`project.py` are tested with pytest, and implemented in ./`test_project.py`. (**Done** ✅)

  - Document usage in `README.md` (installation, running, testing).

### Phase 7: Final Polish & Submission

- **Branch:** `release/v1.0`

- **Tasks:**

  - Clean up repo (remove debug prints, finalize README)

  - Tag release `v1.0`.

  - Prepare submission package for CS50P.

## 🛠️ Work Layout Toward v2.0