# 🏦 Bank Profiles Guide

This guide explains how to add support for new banks and credit cards by creating **profile configs**.  
Profiles define how statements (PDF or CSV) are parsed and normalized into the unified bookkeeping format.

---

## 📖 Overview

Each bank profile is a JSON file stored in:

`config/bank_profiles/{bank}.json`

Profiles describe:
- **Sections** in PDF statements (e.g., Purchases, Payments, Interest)
- **Table Settings** for PDF parsing (tolerances, vertical/horizontal strategies)
- **Column mappings** (which field is at which index)
- **Header validation** (labels to match for robust table discovery)
- **Footer rules** (skip totals, balances via anchor text)
- **Optional CSV format rules** (for banks that export CSVs directly)

All profiles are validated against `config/profile_template.json` (JSON schema).

---

## 🛠️ Steps to Add a New Bank Profile

1. **Collect Statement Details**
   - Layout (single vs two‑column, headers/footers)
   - Section titles
   - Column order
   - Sample rows
   - Parsing quirks (totals, multi‑line descriptions, negative amounts)
   - Filename convention

2. **Fill in the Template**
   - Use `profile_template.json` as a reference.
   - Define `bank_name`, `sections`, and optional `csv_format`.

3. **Save Config**
   - Place the new JSON file in `config/bank_profiles/`.
   - Name it clearly (e.g., `triangle.json`, `cibc.json`, `td_visa.json`).

4. **Validate Config**
   - Run tests to ensure schema compliance:
     ```bash
     pytest -v
     ```
   - Loader will raise errors if the config is invalid.

5. **Add Tests**
   - Create pytest fixtures in `tests/test_pdf_ingest.py`.
   - Simulate sample tables (PDF) or CSV files.
   - Assert parsing results (transaction count, field values, amounts).

---

## 📋 Examples

### Triangle MasterCard (`triangle.json`)

```json
{
  "bank_name": "Triangle MasterCard",
  "skip_pages_by_index": [0],
  "page_header_anchor": "Details of your account summary",
  "table_settings": {
    "vertical_strategy": "explicit",
    "horizontal_strategy": "text"
  },
  "sections": [
    {
      "section_name": "Purchases",
      "match_text": "Purchases",
      "header_labels": ["TRANSACTION\nDATE", "POSTING\nDATE", "TRANSACTION DESCRIPTION", "AMOUNT ($)"],
      "columns": {
        "transaction_date": 0,
        "posting_date": 1,
        "description": 2,
        "amount": 3
      },
      "footer_row_text": "Total purchases",
      "skip_footer_rows": true
    }
  ]
}
```

### CIBC MasterCard (`cibc.json`)

```json
{
  "bank_name": "CIBC Costco MasterCard",
  "sections": [
    {
      "section_name": "Charges and Credits",
      "match_text": "Your new charges and credits",
      "columns": {
        "transaction_date": 0,
        "posting_date": 1,
        "description": 2,
        "spend_category": 3,
        "amount": 4
      },
      "skip_footer_rows": true
    }
  ]
}
```

### TD Visa (`td_visa.json`)

```json
{
  "bank_name": "TD Emerald Flex Rate Visa",
  "sections": [
    {
      "section_name": "Transactions",
      "match_text": "TD EMERALD FLEX RATE CARD",
      "columns": {
        "transaction_date": 0,
        "posting_date": 1,
        "description": 2,
        "amount": 3
      },
      "skip_footer_rows": true
    }
  ],
  "csv_format": {
    "date_format": "MM/DD/YYYY",
    "columns": {
      "transaction_date": 0,
      "description": 1,
      "debit": 2,
      "credit": 3,
      "balance": 4
    },
    "skip_footer_rows": true
  }
}
```

---

## Best Practices

- Always include sample rows in tests to catch quirks.
- Use `skip_footer_rows` to avoid totals and balances.
- Normalize amounts: charges positive, payments negative.
- Keep configs minimal but flexible — only add extra fields if needed (`spend_category`, `annual_interest_rate`).
- Document quirks in commit messages for future maintainers.

---

## 📌 Next Steps

- Add your new profile JSON.
- Write pytest fixtures.
- Commit with a message referencing the issue (e.g., `Closes #42`).
- Push and open a PR.