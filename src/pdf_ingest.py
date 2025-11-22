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
import json
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


def load_bank_profile(bank: str):
    """
    Load a bank profile config from ./config/bank_profiles/<bank>.json.

    Args:
        bank (str): Bank identifier (e.g., 'triangle', 'cibc', 'td_visa').

    Returns:
        dict: Parsed JSON config for the bank.
    """
    profile_path = pathlib.Path(f"./config/bank_profiles/{bank}.json")
    if not profile_path.exists():
        raise FileNotFoundError(f"No profile config found for bank: {bank}")
    with open(profile_path, "r") as f:
        return json.load(f)


def parse_section(table, section_config, source):
    """
    Parse a transaction table using bank profile config.

    Args:
        table (list[list[str]]): Extracted table rows.
        section_config (dict): Section config from bank profile JSON.
        source (str): Source identifier.

    Returns:
        list[dict]: Normalized transaction dictionaries.
    """
    transactions = []
    if not table or len(table) < 2:
        logging.warning("Empty or malformed table in section %s", section_config["section_name"])
        return transactions

    cols = section_config["columns"]
    for row in table[1:]:
        # Skip footer rows if flagged
        if section_config.get("skip_footer_rows", False) and any("total" in cell.lower() for cell in row if cell):
            continue
        
        tx = {
            "source": source,
            "section": section_config["section_name"]
        }
        
        try:
            for field, idx in cols.items():
                if idx < len(row):
                    value = row[idx].strip()
                    # Convert amount to float if field is "amount"
                    if field == "amount":
                        value = value.replace(",", "").replace("$", "").strip()
                        tx[field] = float(value) if value else 0.0
                    else:
                        tx[field] = value
            transactions.append(tx)
        except Exception as e:
            logging.warning("Skipping malformed row in %s: %s | Error: %s", section_config["section_name"], row, e)
            
    logging.info("Parsed %d transactions from section %s", len(transactions), section_config["section_name"])
    return transactions


def parse_pdf(pdf_path: pathlib.Path, bank: str):
    """
    Extract transactions from a PDF using bank profile config.

    Args:
        pdf_path (Path): Path to the PDF file.
        bank (str): Bank identifier.

    Returns:
        list[dict]: All transactions parsed from the PDF.
    """
    transactions = []
    profile = load_bank_profile(bank)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for section in profile["sections"]:
                    if section["match_text"] in text:
                        table = page.extract_table()
                        transactions.extend(parse_section(table, section, profile["bank_name"]))
    except Exception as e:
        logging.error("Failed to parse PDF %s: %s", pdf_path, e)

    logging.info("Extracted %d transactions from %s", len(transactions), pdf_path.name)
    return transactions


def parse_csv(file_path: pathlib.Path, profile: dict):
    """
    Parse TD Visa CSV statement into normalized transactions.
    """
    transactions = []
    with open(file_path, "r") as f:
        for line in f:
            row = line.strip().split(",")
            if not row or len(row) < 5:
                continue

            tx_date = datetime.strptime(row[0], "%m/%d/%Y").strftime("%Y-%m-%d")
            desc = row[1].strip()
            debit = float(row[2]) if row[2] else 0.0
            credit = float(row[3]) if row[3] else 0.0
            amount = debit - credit  # normalize: charges positive, payments negative
            balance = float(row[4]) if row[4] else None

            # Skip footer rows
            if desc in ["PREVIOUS STATEMENT BALANCE", "TOTAL NEW BALANCE"]:
                continue

            transactions.append({
                "transaction_date": tx_date,
                "description": desc,
                "amount": amount,
                "balance": balance,
                "source": profile["bank_name"],
                "section": "Transactions"
            })
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
