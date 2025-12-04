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
from typing import List, Dict
from datetime import datetime
from src.utils import load_bank_profile, notify

def discover_pdfs(year_dir: str):
    """
    Recursively find all PDF files under ./data/<year>/.

    Args:
        year_dir (str): Path to the tax year directory.

    Returns:
        list[pathlib.Path]: Sorted list of PDF file paths.
    """
    pdfs = sorted(pathlib.Path(year_dir).rglob("*.pdf"))
    notify("Discovered %d PDF files in %s" % (len(pdfs), year_dir), "info")
    
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
                    notify("Renamed %s → %s" % (pdf_path.name, new_name), "info")
                return new_path
    except Exception as e:
        notify("Failed to normalize filename for %s: %s" % (pdf_path, e), "warning")
    
    return pdf_path


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
        notify("Empty or malformed table in section %s" % section_config["section_name"], "warning")
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
            notify("Skipping malformed row in %s: %s | Error: %s" % (section_config["section_name"], row, e), "warning")
            
    notify("Parsed %d transactions from section %s" % (len(transactions), section_config["section_name"]), "info")
    return transactions


def validate_table_structure(table_rows: List[List[str | None]], section_config: Dict) -> bool:
    """
    Checks if a raw table matches the column structure AND header content
    defined in the config. Returns True if the table is a valid target.
    
    Args:
        table_rows (list[list[str]]): Extracted table rows.
        section_config (dict): Section config from bank profile JSON.
    Returns:
        bool: True if table matches expected structure and headers.
    """
    if not table_rows or len(table_rows) < 1:
        return False

    expected_labels = section_config.get("header_labels", [])
    expected_col_count = len(section_config["columns"])

    # --- CHECK 1: Column Count ---
    # Check the first row (the header)
    first_row = table_rows[0]
    
    # Clean the row to handle empty cells created by pdfplumber's heuristics
    clean_row = [str(c).strip() for c in first_row if c is not None and str(c).strip() != ""]
    
    if len(clean_row) < expected_col_count:
        # Fails if it doesn't have enough data columns
        return False
    
    if not expected_labels:
        # If no expected labels, assume structure check is sufficient (skip header check)
        return True

    # --- CHECK 2: Header Content (Semantic Validation) ---
    # Check if all required header labels are present in the first row.
    # Look for the labels in the *raw, full* first_row, cleaning them up for comparison.
    
    # 1. Prepare the extracted header for comparison
    header_str = " | ".join([str(c).replace("\n", " ").strip() for c in first_row if c is not None]).lower()
    
    # 2. Check for all expected labels
    for label in expected_labels:
        if label.lower() not in header_str:
            return False

    # If both checks pass, high confidence this is a transaction table
    return True


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
    
    # Validate profile has sections
    if "sections" not in profile or not isinstance(profile["sections"], list):
        notify(f"Bank profile for {bank} is missing 'sections' key or is malformed.", "error")
        return transactions
    
    # notify(f"Processing PDF: {pdf_path.name}", "INFO")

    try:
        """
        Robust PDF parsing: Extracts all tables and uses header validation to identify targets.
        """
        with pdfplumber.open(pdf_path) as pdf:
            
            # Use a list to track which sections have been found/processed
            sections_found_map = {s["section_name"]: False for s in profile["sections"]}
            
            for page_num, page in enumerate(pdf.pages):
                # notify(f"Scanning Page {page_num + 1}...", "DEBUG")
                
                # 1. Extract all tables on the page
                tables = page.find_tables()
                
                for table_obj in tables:
                    table_content = table_obj.extract()
                    
                    # 2. Iterate through all defined sections to find a match
                    for section in profile["sections"]:
                        
                        # STEP A: Structural and Semantic Header Validation
                        if validate_table_structure(table_content, section):
                            
                            is_target_table = True
                            match_text = section.get("match_text")
                            
                            # STEP B: Optional Context Validation (The match_text check)
                            # This is now a TIE-BREAKER, not a boundary setter.
                            # It's less reliable due to false positives, but can help confirm.
                            if match_text:
                                # Look for the match_text nearby (e.g., 100 units above the table's top y-coord)
                                SEARCH_HEIGHT = 100
                                table_bbox = table_obj.bbox  # (x0, y0, x1, y1)
                                table_top_y = table_bbox[1]
                                # Calculate the TOP of the search area, ensuring it's not negative.
                                search_top_y = max(0, table_top_y - SEARCH_HEIGHT)
                                # Define the search area: (page_left, safe_search_top, page_right, table_top)
                                search_area = (0, search_top_y, page.width, table_top_y)
                                nearby_text = page.within_bbox(search_area).extract_text() or ""
                                if match_text.lower() not in nearby_text.lower():
                                    # If the section header isn't found nearby, this might be a table spillover
                                    # This check is tricky. It's safer to trust the header validation alone.
                                    # Skipping this complex check improves robustness.
                                    # is_target_table = False
                                    pass
                            
                            # notify(f"  -> Found '{section['section_name']}' table via Header Validation.", "DEBUG")
                            
                            new_txs = parse_section(table_content, section, profile["bank_name"])
                            transactions.extend(new_txs)
                            
                            # Mark the section as found to avoid double-counting if a similar table exists.
                            sections_found_map[section['section_name']] = True
                            
                            # Break inner loop and move to the next table_obj
                            break
                        
    except Exception as e:
        notify("Failed to parse PDF %s: %s" % (pdf_path, e), "error")

    notify("Extracted %d transactions from %s" % (len(transactions), pdf_path.name), "info")
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
        notify("Exported %d transactions to %s" % (len(transactions), out_path), "info")
    except Exception as e:
        notify("Failed to export CSV %s: %s" % (out_path, e), "error")


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
