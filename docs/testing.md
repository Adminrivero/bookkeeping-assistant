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
  test_classify.py          # Unit tests for classification logic
  test_ingest.py            # Unit tests for CSV ingestion
  test_pdf_ingest.py        # Unit tests for PDF ingestion
  test_pipeline.py          # Pipeline-level tests
  test_project.py           # CLI unit tests
  test_project_smoke.py     # End-to-end CLI smoke tests
  test_rules_integration.py # Integration tests for rules engine
```

---

## Writing New Tests

1. Place new test files under `tests/`.

2. Use `pytest` fixtures (`tmp_path`, `monkeypatch`) for temporary files and mocks.

3. Ensure normalized transaction dicts follow schema:

    ```python
    {
    "transaction_date": str,
    "description": str,
    "amount": float,
    "balance": float | None,
    "source": str,
    "section": str
    }
    ```

4. Add error handling tests (e.g., malformed CSV/PDF).

---

## CI Integration

All tests run automatically via GitHub Actions:

- Workflow: `.github/workflows/tests.yml`
- Triggered on every push and pull request
- Failing tests block merges

---
