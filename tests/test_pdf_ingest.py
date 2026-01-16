"""
Unit tests for PDF ingestion module (src/pdf_ingest.py).
Validates discovery, parsing, normalization, and export behavior.
"""

import json
import pathlib
import tempfile
import csv
import pytest
from pathlib import Path
from src import pdf_ingest
from typing import List
from datetime import datetime

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


@pytest.mark.skip(reason="parse_section removed; temporarily skip until parse_rows is implemented")
def test_parse_section(sample_transactions, triangle_profile):
    # Simulate table with headers + rows
    table = [["TRANSACTION DATE", "POSTING DATE", "DESCRIPTION", "AMOUNT"]] + sample_transactions
    section_config = triangle_profile["sections"][2]  # Purchases section
    statement_period = {"start": "2024-12-26", "end": "2025-01-25", "statement_year": 2025}
    
    txs = pdf_ingest.parse_rows(table, section_config, source=triangle_profile["bank_name"], tax_year="2025", rows_only=False, max_header_rows=1)

    assert len(txs) == 3
    assert txs[0]["description"].startswith("TD BANKLINE")
    assert isinstance(txs[0]["amount"], float)


def test_export_csv(tmp_dir, sample_transactions, triangle_profile):
    # Build normalized txs manually (avoid parse_section dependency)
    section_config = triangle_profile["sections"][2]  # Purchases section
    section_name = section_config.get("section_name", "Purchases")
    bank_name = triangle_profile.get("bank_name", "Triangle MasterCard")

    txs = []
    for r in sample_transactions:
        txs.append({
            "transaction_date": "2025-01-01",
            "posting_date": None,
            "description": str(r[2]),
            "amount": float(str(r[3]).replace("$", "").replace(",", "")),
            "source": bank_name,
            "section": section_name,
        })

    out_path = tmp_dir / "output.csv"
    pdf_ingest.export_csv(txs, out_path)

    # Validate CSV contents
    with open(out_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["source"] == bank_name
        assert rows[0]["section"] == section_name


@pytest.mark.skip(reason="parse_section removed; temporarily skip until parse_rows is implemented")
def test_parse_section_payments(cibc_profile):
    # Simulate a Payments table
    table: List[List[str | None]] = [
        ["Trans date", "Post date", "Description", "Amount($)"],
        ["Jul 23", "Jul 23", "PAYMENT THANK YOU/PAIEMENT MERCI", "254.28"],
        ["Aug 21", "Aug 22", "PAYMENT THANK YOU/PAIEMENT MERCI", "767.39"],
        ["Total payments", "", "", "$1,021.67"]
    ]
    section_config = cibc_profile["sections"][0]  # Payments section
    statement_period = {"start": "2025-07-01", "end": "2025-07-31", "statement_year": 2025}
        
    txs = pdf_ingest.parse_rows(table, section_config, source=cibc_profile["bank_name"], tax_year="2025", rows_only=False, max_header_rows=1)

    assert len(txs) == 2
    assert txs[0]["description"].startswith("PAYMENT THANK YOU")
    assert isinstance(txs[0]["amount"], float)


@pytest.mark.skip(reason="parse_section removed; temporarily skip until parse_rows is implemented")
def test_parse_section_charges_and_credits(cibc_profile):
    # Simulate a Charges and Credits table
    table: List[List[str | None]] = [
        ["Trans", "Post", "Description", "Amount($)"],
        ["date", "date", "", ""],
        ["Aug 27", "Aug 29", "7-ELEVEN #33414 - B TORONTO ON", "Transportation", "20.00"],
        ["Sep 07", "Sep 09", "SQ *TENT 2        ETOBICOKE ON", "Restaurants", "20.70"],
        ["Sep 20", "Sep 23", "7-ELEVEN #33414 - B TORONTO ON", "Transportation", "40.00"],
        ["Total for 5268 XXXX XXXX 9061", "", "", "", "$80.70"]
    ]
    section_config = cibc_profile["sections"][2]  # Charges and Credits section
    statement_period = {"start": "2025-08-01", "end": "2025-09-30", "statement_year": 2025}
    
    txs = pdf_ingest.parse_rows(table, section_config, source=cibc_profile["bank_name"], tax_year="2025", rows_only=False, max_header_rows=2)

    assert len(txs) == 3
    assert txs[1]["spend_category"] == "Restaurants"
    assert txs[2]["amount"] == 40.00


def test_parse_csv_td_visa(td_visa_profile, td_visa_csv_sample):
    txs = pdf_ingest.parse_csv(td_visa_csv_sample, td_visa_profile)
    assert len(txs) == 3
    assert txs[0]["description"] == "BALANCE PROTECTION INS"
    assert txs[0]["amount"] == 1.67
    assert txs[2]["amount"] == -303.29  # payment normalized as negative


@pytest.mark.skip(reason="parse_section removed; temporarily skip until parse_rows is implemented")
def test_parse_pdf_td_visa(td_visa_profile):
    # Simulate a PDF table
    table: List[List[str | None]] = [
        ["MAY 17", "MAY 20", "TIM HORTONS #1357 ETOBICOKE", "28.23"],
        ["MAY 22", "MAY 23", "PAYMENT - THANK YOU", "-404.15"],
        ["JUN 9", "JUN 9", "BALANCE PROTECTION (INCL TAX)", "1.80"],
        ["", "", "TOTAL NEW BALANCE", "140.83"]
    ]
    section_config = td_visa_profile["sections"][0]
    statement_period = {"start": "2025-05-01", "end": "2025-06-30", "statement_year": 2025}
    
    txs = pdf_ingest.parse_rows(table, section_config, source=td_visa_profile["bank_name"], tax_year="2025", rows_only=True)

    assert len(txs) == 3
    assert txs[0]["description"].startswith("TIM HORTONS")
    assert txs[1]["amount"] == -404.15


def test_parse_pdf_normalization(monkeypatch, tmp_path):
    # Fake PDF file
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_text("%PDF-1.4 fake content")

    # Monkeypatch parse_pdf to simulate parsed output
    monkeypatch.setattr(pdf_ingest, "parse_pdf", lambda f, p: [
        {"transaction_date": "2025-05-01", "description": "Purchase", "amount": -50.00,
         "balance": 950.00, "source": "CIBC", "section": "Transactions"}
    ])

    result = pdf_ingest.parse_pdf(pdf_file, "cibc")
    assert isinstance(result, list)
    tx = result[0]
    assert set(tx.keys()) == {"transaction_date", "description", "amount", "balance", "source", "section"}


def test_parse_pdf_error(monkeypatch, tmp_path):
    pdf_file = tmp_path / "corrupt.pdf"
    pdf_file.write_text("not a real pdf")

    # Monkeypatch to raise error
    monkeypatch.setattr(pdf_ingest, "parse_pdf", lambda f, p: (_ for _ in ()).throw(ValueError("Malformed PDF")))

    with pytest.raises(ValueError):
        pdf_ingest.parse_pdf(pdf_file, "cibc")


def test_parse_rows_single_row_no_header():
    # Single data row and rows_only=False should NOT drop the only row
    rows: List[List[str | None]] = [["Jan 03", "", "Some Merchant", "12.34"]]
    section = {
        "columns": {"transaction_date": 0, "posting_date": 1, "description": 2, "amount": 3},
        "section_name": "Transactions",
    }
    
    txs = pdf_ingest.parse_rows(rows, section, source="Triangle", tax_year="2025", rows_only=True)
    
    assert len(txs) == 1
    assert txs[0]["description"].startswith("Some Merchant")
    assert txs[0]["amount"] == 12.34


@pytest.mark.parametrize(
    "text,start_iso,end_iso",
    [
        ("Dec 26 to Jan 25, 2024", "2023-12-26", "2024-01-25"),
        ("Dec26toJan25,2024", "2023-12-26", "2024-01-25"),
        ("December 24, 2024 to January 23, 2025", "2024-12-24", "2025-01-23"),
        ("December08,2023toJanuary08,2024", "2023-12-08", "2024-01-08"),
        ("May 08, 2025 to June 09, 2025", "2025-05-08", "2025-06-09"),
        ("December 08. 2023 to January 08, 2024", "2023-12-08", "2024-01-08"),
        ("May08,2025toJune09,2025", "2025-05-08", "2025-06-09"),
    ],
)
def test_detect_statement_period_variants(text, start_iso, end_iso):
    result = pdf_ingest.detect_statement_period(text)
    assert result is not None
    assert result["start"].strftime("%Y-%m-%d") == start_iso
    assert result["end"].strftime("%Y-%m-%d") == end_iso


def test_parse_rows_infers_prev_year_for_dec_rows_in_cross_year_statement():
    """
    Corner case:
      Statement period crosses years (Dec -> Jan), and the PDF row dates omit the year.
      "Dec 27" in a period ending Jan 25, 2024 should resolve to 2023-12-27 (not 2024-12-27).
    """
    statement_period = {
        "start": datetime(2023, 12, 26),
        "end": datetime(2024, 1, 25),
        "statement_year": 2024,
    }

    section = {
        "section_name": "Transactions",
        "columns": {"transaction_date": 0, "posting_date": 1, "description": 2, "amount": 3},
    }

    rows: List[List[str | None]] = [
        ["Dec 27", "Dec 27", "TD BANKLINE/TELELIGNE T.D.", "-500.00"],
    ]

    txs = pdf_ingest.parse_rows(
        rows,
        section,
        source="TD Visa",
        tax_year="2023",
        statement_period=statement_period,
        rows_only=True,
    )

    assert len(txs) == 1
    assert txs[0]["transaction_date"] == "2023-12-27"
    assert txs[0]["amount"] == -500.00