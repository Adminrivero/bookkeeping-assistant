# src/pdf_ingest.py

import pathlib
import pdfplumber
import csv
import re
from datetime import datetime

def discover_pdfs(year_dir: str):
    """Recursively find all PDF files under ./data/<year>/"""
    return sorted(pathlib.Path(year_dir).rglob("*.pdf"))

def normalize_filename(pdf_path: pathlib.Path, bank: str):
    """Ensure filename follows <bank>-<month>.pdf convention by reading statement date."""
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ""
        match = re.search(r"Statement date:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
        if match:
            date_obj = datetime.strptime(match.group(1), "%B %d, %Y")
            month_str = date_obj.strftime("%b").lower()
            new_name = f"{bank}-{month_str}.pdf"
            new_path = pdf_path.with_name(new_name)
            if pdf_path.name != new_name:
                pdf_path.rename(new_path)
            return new_path
    return pdf_path

def parse_section(table, section_name, source):
    """Parse a single transaction table into normalized dicts."""
    transactions = []
    if not table or len(table) < 2:
        return transactions
    headers = [h.strip().lower() for h in table[0]]
    for row in table[1:]:
        # Skip footer rows like "Total purchases"
        if "total" in row[0].lower():
            continue
        try:
            tx_date = row[0].strip()
            post_date = row[1].strip()
            desc = row[2].strip()
            amt_str = row[3].replace(",", "").replace("$", "").strip()
            amount = float(amt_str) if amt_str else 0.0
            transactions.append({
                "transaction_date": datetime.strptime(tx_date, "%b %d"),  # adjust format if needed
                "posting_date": post_date,
                "description": desc,
                "amount": amount,
                "source": source,
                "section": section_name
            })
        except Exception:
            continue
    return transactions

def parse_pdf(pdf_path: pathlib.Path, source: str):
    """Extract transactions from a Triangle MasterCard PDF."""
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "Payments received" in text:
                table = page.extract_table()
                transactions.extend(parse_section(table, "Payments", source))
            if "Returns and other credits" in text:
                table = page.extract_table()
                transactions.extend(parse_section(table, "Credits", source))
            if "Purchases" in text:
                table = page.extract_table()
                transactions.extend(parse_section(table, "Purchases", source))
            if "Interest charges" in text:
                table = page.extract_table()
                transactions.extend(parse_section(table, "Interest", source))
    return transactions

def export_csv(transactions, out_path: pathlib.Path):
    """Write transactions to CSV."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["transaction_date","posting_date","description","amount","source","section"])
        writer.writeheader()
        for tx in transactions:
            writer.writerow({
                "transaction_date": tx["transaction_date"].strftime("%Y-%m-%d") if isinstance(tx["transaction_date"], datetime) else tx["transaction_date"],
                "posting_date": tx["posting_date"],
                "description": tx["description"],
                "amount": tx["amount"],
                "source": tx["source"],
                "section": tx["section"]
            })

def ingest_year(year: str, bank: str = "triangle"):
    """Main entrypoint: discover, normalize, parse, and export all PDFs for a tax year."""
    pdfs = discover_pdfs(f"./data/{year}/")
    all_tx = []
    for pdf in pdfs:
        normalized_pdf = normalize_filename(pdf, bank)
        tx = parse_pdf(normalized_pdf, bank)
        export_csv(tx, pathlib.Path(f"./output/{year}/{bank}/{normalized_pdf.stem}.csv"))
        all_tx.extend(tx)
    # unified CSV
    export_csv(sorted(all_tx, key=lambda x: x["transaction_date"]), pathlib.Path(f"./output/{year}/credit_cards.csv"))
