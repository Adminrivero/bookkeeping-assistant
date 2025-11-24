"""
Unit tests for PDF ingestion module (src/pdf_ingest.py).
Validates discovery, parsing, normalization, and export behavior.
"""

import json
import pathlib
import tempfile
import csv
import pytest
from src import pdf_ingest

# --- Fixtures ---

@pytest.fixture
def tmp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp:
        yield pathlib.Path(tmp)

@pytest.fixture
def sample_transactions():
    """Mock transaction rows simulating parsed PDF tables."""
    return [
        ["Dec 27", "Dec 27", "TD BANKLINE/TELELIGNE T.", "-123.45"],
        ["Jan 03", "Jan 05", "THE HOME DEPOT #7011", "456.78"],
        ["Jan 25", "Jan 25", "INTEREST CHARGES", "12.34"],
    ]

@pytest.fixture
def triangle_profile():
    """Load Triangle MasterCard profile config from JSON."""
    profile_path = pathlib.Path("./config/bank_profiles/triangle.json")
    with open(profile_path, "r") as f:
        return json.load(f)

@pytest.fixture
def cibc_profile():
    """Load CIBC MasterCard profile config from JSON."""
    profile_path = pathlib.Path("./config/bank_profiles/cibc.json")
    with open(profile_path, "r") as f:
        return json.load(f)

@pytest.fixture
def td_visa_profile():
    """Load TD Visa profile config from JSON."""
    profile_path = pathlib.Path("./config/bank_profiles/td_visa.json")
    with open(profile_path, "r") as f:
        return json.load(f)

@pytest.fixture
def td_visa_csv_sample(tmp_path):
    """Create a temporary TD Visa CSV sample file."""
    csv_content = """06/09/2025,BALANCE PROTECTION INS,1.67,,140.83
                06/09/2025,BALANCE PROTECTION TAX,0.13,,139.16
                05/30/2025,PAYMENT - THANK YOU,,303.29,0.00"""
    csv_file = tmp_path / "td_visa_sample.csv"
    csv_file.write_text(csv_content)
    return csv_file

# --- Tests ---

def test_discover_pdfs(tmp_dir):
    # Create dummy PDF files
    pdf1 = tmp_dir / "triangle-jan.pdf"
    pdf2 = tmp_dir / "triangle-feb.pdf"
    pdf1.touch()
    pdf2.touch()

    pdfs = pdf_ingest.discover_pdfs(tmp_dir)
    assert len(pdfs) == 2
    assert pdf1 in pdfs and pdf2 in pdfs

def test_parse_section(sample_transactions, triangle_profile):
    # Simulate table with headers + rows
    table = [["TRANSACTION DATE", "POSTING DATE", "DESCRIPTION", "AMOUNT"]] + sample_transactions
    section_config = triangle_profile["sections"][2]  # Purchases section
    txs = pdf_ingest.parse_section(table, section_config, triangle_profile["bank_name"])

    assert len(txs) == 3
    assert txs[0]["description"].startswith("TD BANKLINE")
    assert isinstance(txs[0]["amount"], float)

def test_export_csv(tmp_dir, sample_transactions, triangle_profile):
    # Convert sample rows into normalized dicts
    table = [["TRANSACTION DATE", "POSTING DATE", "DESCRIPTION", "AMOUNT"]] + sample_transactions
    section_config = triangle_profile["sections"][2]  # Purchases section
    txs = pdf_ingest.parse_section(table, section_config, triangle_profile["bank_name"])

    out_path = tmp_dir / "output.csv"
    pdf_ingest.export_csv(txs, out_path)

    # Validate CSV contents
    with open(out_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["source"] == "Triangle MasterCard"
        assert rows[0]["section"] == "Purchases"

def test_parse_section_payments(cibc_profile):
    # Simulate a Payments table
    table = [
        ["Trans date", "Post date", "Description", "Amount($)"],
        ["Jul 23", "Jul 23", "PAYMENT THANK YOU/PAIEMENT MERCI", "254.28"],
        ["Aug 21", "Aug 22", "PAYMENT THANK YOU/PAIEMENT MERCI", "767.39"],
        ["Total payments", "", "", "$1,021.67"]
    ]

    section_config = cibc_profile["sections"][0]  # Payments section
    txs = pdf_ingest.parse_section(table, section_config, cibc_profile["bank_name"])

    assert len(txs) == 2
    assert txs[0]["description"].startswith("PAYMENT THANK YOU")
    assert isinstance(txs[0]["amount"], float)

def test_parse_section_interest(cibc_profile):
    # Simulate an Interest table
    table = [
        ["Trans date", "Post date", "Description", "Annual interest rate", "Amount($)"],
        ["Oct 23", "Oct 23", "REGULAR PURCHASES", "20.75%", "8.11"],
        ["Total interest this period", "", "", "", "$8.11"]
    ]

    section_config = cibc_profile["sections"][1]  # Interest section
    txs = pdf_ingest.parse_section(table, section_config, cibc_profile["bank_name"])

    assert len(txs) == 1
    assert txs[0]["description"] == "REGULAR PURCHASES"
    assert txs[0]["amount"] == 8.11

def test_parse_section_charges_and_credits(cibc_profile):
    # Simulate a Charges and Credits table
    table = [
        ["Trans date", "Post date", "Description", "Spend Categories", "Amount($)"],
        ["Aug 27", "Aug 29", "7-ELEVEN #33414 - B TORONTO ON", "Transportation", "20.00"],
        ["Sep 07", "Sep 09", "SQ *TENT 2        ETOBICOKE ON", "Restaurants", "20.70"],
        ["Sep 20", "Sep 23", "7-ELEVEN #33414 - B TORONTO ON", "Transportation", "40.00"],
        ["Total for 5268 XXXX XXXX 9061", "", "", "", "$80.70"]
    ]

    section_config = cibc_profile["sections"][2]  # Charges and Credits section
    txs = pdf_ingest.parse_section(table, section_config, cibc_profile["bank_name"])

    assert len(txs) == 3
    assert txs[1]["spend_category"] == "Restaurants"
    assert txs[2]["amount"] == 40.00

def test_parse_csv_td_visa(td_visa_profile, td_visa_csv_sample):
    txs = pdf_ingest.parse_csv(td_visa_csv_sample, td_visa_profile)
    assert len(txs) == 3
    assert txs[0]["description"] == "BALANCE PROTECTION INS"
    assert txs[0]["amount"] == 1.67
    assert txs[2]["amount"] == -303.29  # payment normalized as negative

def test_parse_pdf_td_visa(td_visa_profile):
    # Simulate a PDF table
    table = [
        ["TRANSACTION DATE", "POSTING DATE", "ACTIVITY DESCRIPTION", "AMOUNT($)"],
        ["MAY 17", "MAY 20", "TIM HORTONS #1357 ETOBICOKE", "28.23"],
        ["MAY 22", "MAY 23", "PAYMENT - THANK YOU", "-404.15"],
        ["JUN 9", "JUN 9", "BALANCE PROTECTION (INCL TAX)", "1.80"],
        ["", "", "TOTAL NEW BALANCE", "140.83"]
    ]

    section_config = td_visa_profile["sections"][0]
    txs = pdf_ingest.parse_section(table, section_config, td_visa_profile["bank_name"])

    assert len(txs) == 3
    assert txs[0]["description"].startswith("TIM HORTONS")
    assert txs[1]["amount"] == -404.15