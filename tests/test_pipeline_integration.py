import pathlib
import pytest
from src.pipeline import ingest_statement, run_pipeline
from src.utils import load_rules

@pytest.fixture
def fake_data_dir(tmp_path):
    """Create a fake data directory with account CSV and bank subfolders."""
    year_dir = tmp_path / "2025"
    year_dir.mkdir()

    # Root account CSV
    account_csv = year_dir / "account.csv"
    account_csv.write_text("2025-05-01,Deposit,1000.00\n2025-05-02,Withdrawal,-200.00")

    # Bank subfolder with CSV
    triangle_dir = year_dir / "triangle"
    triangle_dir.mkdir()
    triangle_csv = triangle_dir / "triangle_may.csv"
    triangle_csv.write_text("05/01/2025,Merchant,50.00,,950.00")

    # Bank subfolder with PDF (simulate by suffix only)
    cibc_dir = year_dir / "cibc"
    cibc_dir.mkdir()
    cibc_pdf = cibc_dir / "cibc_may.pdf"
    cibc_pdf.write_text("%PDF-1.4 fake content")

    return year_dir, account_csv, triangle_csv, cibc_pdf

def test_ingest_statement_account_and_banks(fake_data_dir, monkeypatch):
    year_dir, account_csv, triangle_csv, cibc_pdf = fake_data_dir

    # Monkeypatch pdf_ingest to avoid real PDF parsing
    from src import pdf_ingest
    monkeypatch.setattr(pdf_ingest, "parse_pdf", lambda f, p: [
        {"transaction_date": "2025-05-01", "description": "PDF Tx", "amount": 123.45,
         "balance": None, "source": "CIBC", "section": "Transactions"}
    ])

    # Monkeypatch csv_ingest to simplify parsing
    from src import csv_ingest
    monkeypatch.setattr(csv_ingest, "parse_csv", lambda f, p: [
        {"transaction_date": "2025-05-01", "description": "CSV Tx", "amount": 50.00,
         "balance": 950.00, "source": "Triangle", "section": "Transactions"}
    ])

    # Monkeypatch load_csv for account CSVs
    from src.ingest import load_csv
    monkeypatch.setattr("src.ingest.load_csv", lambda f: [
        {"transaction_date": "2025-05-01", "description": "Deposit", "amount": 1000.00,
         "balance": None, "source": "Account", "section": "Transactions"}
    ])

    # Ingest account CSV
    txs_account = ingest_statement(account_csv, "account")
    assert txs_account[0]["source"] == "Account"
    assert txs_account[0]["amount"] == 1000.00

    # Ingest triangle CSV
    txs_triangle = ingest_statement(triangle_csv, "triangle")
    assert txs_triangle[0]["description"] == "CSV Tx"

    # Ingest cibc PDF
    txs_cibc = ingest_statement(cibc_pdf, "cibc")
    assert txs_cibc[0]["description"] == "PDF Tx"

    # Combine and run pipeline
    rules = load_rules(pathlib.Path("config/allocation_rules.json"))
    wb = run_pipeline(txs_account + txs_triangle + txs_cibc, "config/allocation_rules.json", show_progress=False)
    assert wb is not None
