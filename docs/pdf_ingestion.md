# 📄 PDF Ingestion Guide

Bookkeeping Assistant supports ingestion of both **CSV** and **PDF** statements. The system automatically detects file type and routes to the correct ingestor, ensuring normalized output across formats.

---

## 📂 Directory Structure

Organize your input files under `data/{year}/`:

```bash
data/
  2025/
    account.csv                # Root account activity (chequing/savings)
    triangle/                   # Credit card statements (Triangle MasterCard)
      triangle_jan.pdf
      triangle_feb.pdf
    cibc/                       # Credit card statements (CIBC MasterCard)
      cibc_mar.csv
      cibc_apr.pdf
```

- **Root account CSVs** (`account.csv`) are always present.
- **Bank subfolders** (`triangle/`, `cibc/`, etc.) contain monthly statements in either CSV or PDF format.
- The program ingests all files found in these directories automatically.

---

## ▶️ CLI Usage

Run the assistant by specifying the year and one or more bank profiles:

```bash
python project.py -y 2025 -b triangle cibc
```

This will:

- Ingest root account CSVs in `data/2025/`.
- Ingest all statements (CSV or PDF) under `data/2025/triangle/` and `data/2025/cibc/`.
- Normalize transactions and export them to Excel.

Output file:

```bash
output/2025/bookkeeping_2025.xlsx
```

---

## 🏦 Bank Profiles

Each bank has a profile config in `config/bank_profiles/`. Profiles define column mappings and parsing rules for CSV/PDF ingestion.

To add a new bank:

1. Create a JSON config with column mappings and section rules.
2. Place it in `config/bank_profiles/`.
3. Reference it by name with `--bank` or `-b`.

Example:

```bash
python project.py -y 2025 -b td_visa
```

---

## 🔄 Normalization

Regardless of input format (CSV or PDF), transactions are normalized to a unified schema:

```json
{
  "transaction_date": "2025-05-01",
  "description": "Purchase at Merchant",
  "amount": -50.00,
  "balance": 950.00,
  "source": "Triangle",
  "section": "Transactions"
}
```

This ensures consistent downstream classification and export.

---

## ⚠️ Error Handling

- **Unsupported file types** → Raises `ValueError`.

- **Missing files** → Raises `FileNotFoundError`.

- **Malformed PDFs** → Raises `ValueError` during parsing.

Errors are reported via the CLI with clear messages.

---

## 📊 Example Workflow

Input:

- `data/2025/account.csv`

- `data/2025/triangle/*.pdf`

- `data/2025/cibc/*.csv`

Command:

```bash
python project.py -y 2025 -b triangle cibc
```

Output:

- `output/2025/bookkeeping_2025.xlsx`

---
