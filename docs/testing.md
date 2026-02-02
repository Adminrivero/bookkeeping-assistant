# 🧪 Testing Guide

Bookkeeping Assistant uses **pytest** for unit, integration, and smoke tests.  
Tests ensure ingestion, classification, pipeline, and export logic remain stable across versions.

---

## Running Tests

From the project root:

```bash
pytest -v
```

- `-v` -> verbose output
- `-s` -> show print/log output
- `-k <pattern>` -> run tests matching a name pattern

---

## Test Structure

```
tests/
  tests/rule_generator/       # Rule-generator/schema/validator unit tests
    test_rule_schema_validation.py
  test_classify.py            # Unit tests for classification logic
  test_ingest.py              # Unit tests for CSV ingestion
  test_pdf_ingest.py          # Unit tests for PDF ingestion
  test_pipeline.py            # Pipeline-level tests
  test_project.py             # CLI unit tests
  test_project_smoke.py       # End-to-end CLI smoke tests
  test_rules_integration.py   # Integration tests for rules engine
```

---

## Writing New Tests

1. Place new test files under `tests/`. For rule-generator or schema work, place tests under `tests/rule_generator/` to mirror `src/rule_generator/`.

2. Use pytest fixtures (`tmp_path`, `monkeypatch`) for temporary files and mocks.

3. Ensure normalized transaction dicts follow the canonical shape (see src/utils.normalize_tx_to_canonical_shape):

    ```python
    {
      "Date": "YYYY-MM-DD" | None,
      "Description": "string",
      "Debit": float >= 0.0,
      "Credit": float >= 0.0,
      "Balance": float | None,
      "source": "string",
      "raw_fields": { ... }  # optional
    }
    ```

4. Add error handling tests (e.g., malformed CSV/PDF).

---

## How to run focused tests

- Run rule/schema tests only:
```bash
pytest tests/rule_generator -q
```

- Run the schema validation test:
```bash
pytest tests/rule_generator/test_rule_schema_validation.py -q
```

--- 

## CI Integration

All tests run automatically via GitHub Actions:

- Workflow: `.github/workflows/tests.yml`
- Triggered on every push and pull request
- Failing tests block merges
- Ensure schema validation test is included in CI so schema drift is detected early

---
