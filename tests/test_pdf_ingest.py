"""
Unit tests for PDF ingestion module (src/pdf_ingest.py).
Validates discovery, parsing, normalization, and export behavior.
"""

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


def test_parse_section(sample_transactions):
    # Simulate table with headers + rows
    table = [["TRANSACTION DATE", "POSTING DATE", "DESCRIPTION", "AMOUNT"]] + sample_transactions
    txs = pdf_ingest.parse_section(table, "Purchases", "Triangle MasterCard")

    assert len(txs) == 3
    assert txs[0]["description"].startswith("TD BANKLINE")
    assert isinstance(txs[0]["amount"], float)


def test_export_csv(tmp_dir, sample_transactions):
    # Convert sample rows into normalized dicts
    table = [["TRANSACTION DATE", "POSTING DATE", "DESCRIPTION", "AMOUNT"]] + sample_transactions
    txs = pdf_ingest.parse_section(table, "Purchases", "Triangle MasterCard")

    out_path = tmp_dir / "output.csv"
    pdf_ingest.export_csv(txs, out_path)

    # Validate CSV contents
    with open(out_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["source"] == "Triangle MasterCard"
        assert rows[0]["section"] == "Purchases"
