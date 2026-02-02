# 📑 Config Schema Guide

Bank profile configs are validated against `config/schemas/bank_profile_schema.json`.  
This ensures consistency across all banks and prevents subtle errors.

---

## 🧩 Top-Level Fields

- **`bank_name`** *(string, required)*  
  Human-readable name of the bank/card.  
  Example: `"CIBC Costco MasterCard"`

- **`skip_pages_by_index`** *(array, optional)*  
  List of 0-based page indices to ignore (e.g., promotional pages).  
  Example: `[0]`

- **`page_header_anchor`** *(string, optional)*  
  Text anchor to identify valid statement pages.

- **`table_settings`** *(object, optional)*  
  Advanced `pdfplumber` settings for table extraction.  
  - `vertical_strategy` *(string)*: `"lines"`, `"text"`, or `"explicit"`.
  - `horizontal_strategy` *(string)*: `"lines"`, `"text"`, or `"explicit"`.
  - `explicit_vertical_lines` *(array)*: List of x-coordinates (when using `"explicit"` strategy).
  - `text_x_tolerance`, `text_y_tolerance`, `intersection_tolerance` *(number)*: Extraction sensitivity.

- **`sections`** *(array, required)*  
  Defines how to parse PDF statement tables.  
  Each section is an object with:
  - `section_name` *(string)* → Logical name (e.g., Purchases, Payments).  
  - `match_text` *(string)* → Anchor text in PDF to identify section.  
  - `header_labels` *(array, optional)* → List of header strings to validate table structure.
  - `columns` *(object)* → Mapping of field names to column indices.  
    - Keys: any valid field name (`transaction_date`, `posting_date`, `description`, `amount`, `spend_category`, etc.).  
    - Values: integer index (0-based).  
  - `footer_row_text` *(string, optional)* → Anchor text to identify the end of a section.
  - `skip_footer_rows` *(boolean, optional)* → Skip totals or summary rows.

- **`csv_format`** *(object, optional)*  
  Defines rules for CSV ingestion (for banks that export CSVs).  
  - `date_format` *(string)* → `"YYYY-MM-DD"` or `"MM/DD/YYYY"`.  
  - `columns` *(object)* → Mapping of CSV fields to column indices.  
    - Example: `{"transaction_date": 0, "description": 1, "debit": 2, "credit": 3, "balance": 4}`  
  - `skip_footer_rows` *(boolean, optional)* → Skip totals or balances.

---

## ✅ Example Configs

### Triangle MasterCard
```json
{
  "bank_name": "Triangle MasterCard",
  "skip_pages_by_index": [0],
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

### TD Visa (with CSV support)

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

## 📌 Best Practices

- Always validate configs with `jsonschema` before committing.
- Keep field names consistent (`transaction_date`, `posting_date`, `description`, `amount`).
- Use `skip_footer_rows` to avoid totals and balances.
- Normalize amounts: charges positive, payments negative.
- Document quirks in commit messages for future maintainers.