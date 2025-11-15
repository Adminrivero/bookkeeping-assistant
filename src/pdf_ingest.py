"""
PDF Ingestion Module for Credit Card Statements
-----------------------------------------------
This module discovers, normalizes, parses, and exports transactions
from credit card statement PDFs (e.g., Triangle MasterCard).
"""

import pathlib
import pdfplumber
import csv
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def discover_pdfs(year_dir: str):
    """
    Recursively find all PDF files under ./data/<year>/.

    Args:
        year_dir (str): Path to the tax year directory.

    Returns:
        list[pathlib.Path]: Sorted list of PDF file paths.
    """
    pdfs = sorted(pathlib.Path(year_dir).rglob("*.pdf"))
    logging.info("Discovered %d PDF files in %s", len(pdfs), year_dir)
    return pdfs


def normalize_filename(pdf_path: pathlib.Path, bank: str):
    """
    Ensure filename follows <bank>-<month>.pdf convention by reading statement date.

    Args:
        pdf_path (Path): Path to the PDF file.
        bank (str): Bank identifier (e.g., 'triangle').

    Returns:
        Path: Normalized file path.
    """
    try:
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
                    logging.info("Renamed %s → %s", pdf_path.name, new_name)
                return new_path
    except Exception as e:
        logging.warning("Failed to normalize filename for %s: %s", pdf_path, e)
    return pdf_path


def parse_section(table, section_name, source):
    """
    Parse a single transaction table into normalized dicts.

    Args:
        table (list[list[str]]): Extracted table rows.
        section_name (str): Section label (Payments, Purchases, etc.).
        source (str): Source identifier (e.g., 'Triangle MasterCard').

    Returns:
        list[dict]: Normalized transaction dictionaries.
    """
    transactions = []
    if not table or len(table) < 2:
        logging.warning("Empty or malformed table in section %s", section_name)
        return transactions

    for row in table[1:]:
        if not row or "total" in row[0].lower():
            continue
        try:
            tx_date = row[0].strip()
            post_date = row[1].strip()
            desc = row[2].strip()
            amt_str = row[3].replace(",", "").replace("$", "").strip()
            amount = float(amt_str) if amt_str else 0.0
            transactions.append({
                "transaction_date": tx_date,
                "posting_date": post_date,
                "description": desc,
                "amount": amount,
                "source": source,
                "section": section_name
            })
        except Exception as e:
            logging.warning("Skipping malformed row in %s: %s | Error: %s", section_name, row, e)
    logging.info("Parsed %d transactions from section %s", len(transactions), section_name)
    return transactions


def parse_pdf(pdf_path: pathlib.Path, source: str):
    """
    Extract transactions from a Triangle MasterCard PDF.

    Args:
        pdf_path (Path): Path to the PDF file.
        source (str): Source identifier.

    Returns:
        list[dict]: All transactions parsed from the PDF.
    """
    transactions = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if "Payments received" in text:
                    transactions.extend(parse_section(page.extract_table(), "Payments", source))
                if "Returns and other credits" in text:
                    transactions.extend(parse_section(page.extract_table(), "Credits", source))
                if "Purchases" in text:
                    transactions.extend(parse_section(page.extract_table(), "Purchases", source))
                if "Interest charges" in text:
                    transactions.extend(parse_section(page.extract_table(), "Interest", source))
    except Exception as e:
        logging.error("Failed to parse PDF %s: %s", pdf_path, e)
    logging.info("Extracted %d transactions from %s", len(transactions), pdf_path.name)
    return transactions


def export_csv(transactions, out_path: pathlib.Path):
    """
    Write transactions to CSV.

    Args:
        transactions (list[dict]): List of transaction dicts.
        out_path (Path): Output CSV path.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["transaction_date","posting_date","description","amount","source","section"])
            writer.writeheader()
            for tx in transactions:
                writer.writerow(tx)
        logging.info("Exported %d transactions to %s", len(transactions), out_path)
    except Exception as e:
        logging.error("Failed to export CSV %s: %s", out_path, e)


def ingest_year(year: str, bank: str = "triangle"):
    """
    Main entrypoint: discover, normalize, parse, and export all PDFs for a tax year.

    Args:
        year (str): Tax year (e.g., '2024').
        bank (str): Bank identifier (default 'triangle').
    """
    pdfs = discover_pdfs(f"./data/{year}/")
    all_tx = []
    for pdf in pdfs:
        normalized_pdf = normalize_filename(pdf, bank)
        tx = parse_pdf(normalized_pdf, bank)
        export_csv(tx, pathlib.Path(f"./output/{year}/{bank}/{normalized_pdf.stem}.csv"))
        all_tx.extend(tx)
    # unified CSV
    export_csv(sorted(all_tx, key=lambda x: x["transaction_date"]), pathlib.Path(f"./output/{year}/credit_cards.csv"))
