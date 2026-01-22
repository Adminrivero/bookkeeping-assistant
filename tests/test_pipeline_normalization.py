import csv
import pytest
from datetime import datetime
from pathlib import Path
from src import pdf_ingest
from src.csv_ingest import parse_csv
from src.ingest import load_csv
from src.utils import normalize_tx_to_canonical_shape

def _assert_canonical_shape(tx, source_expected: str):
    assert set(tx.keys()) == {"Date", "Description", "Debit", "Credit", "Balance", "source"}
    assert isinstance(tx["Description"], str)
    assert isinstance(tx["Debit"], float)
    assert isinstance(tx["Credit"], float)
    assert (tx["Balance"] is None) or isinstance(tx["Balance"], float)
    assert tx["source"] == source_expected


def test_bank_account_load_csv_shape(tmp_path: Path):
    """
    Ensure load_csv returns canonical bank-account-shaped transactions:
      {Date, Description, Debit, Credit, Balance, source="bank_account"}.
    """
    csv_path = tmp_path / "account_activity.csv"
    # Header-style CSV (typical bank account export)
    csv_path.write_text(
        "Date,Description,Debit,Credit,Balance\n"
        "2024-01-02,TIM HORTONS #08 _F,4.72,0.00,1000.00\n"
        "2024-01-03,LCBO/RAO #0426 _F,15.70,0.00,984.30\n",
        encoding="utf-8",
    )

    txs = load_csv(str(csv_path))
    assert len(txs) == 2

    for tx in txs:
        _assert_canonical_shape(tx, source_expected="bank_account")
        assert tx["Date"] in ("2024-01-02", "2024-01-03")
        # Debit must be non-negative; credit is zero in this sample
        assert tx["Debit"] >= 0
        assert tx["Credit"] == 0.0


def test_normalize_tx_to_canonical_shape_card_amount():
    """
    Ensure card-style tx (transaction_date + signed amount) is normalized correctly.
    """
    raw = {
        "transaction_date": "2024-01-02",
        "description": "CASHADV./AV.DEFONDS",
        "amount": 100.0,
        "balance": None,
    }

    tx = normalize_tx_to_canonical_shape(raw, source_type="credit_card")

    _assert_canonical_shape(tx, source_expected="credit_card")
    assert tx["Date"] == "2024-01-02"
    assert tx["Description"] == "CASHADV./AV.DEFONDS"
    assert tx["Debit"] == 100.0
    assert tx["Credit"] == 0.0
    assert tx["Balance"] is None


def test_profile_csv_normalized_shape(monkeypatch, tmp_path: Path):
    """
    Create a fake CSV + profile and ensure parse_csv returns canonical credit-card-shaped txs.
    """
    csv_path = tmp_path / "card_statement.csv"
    csv_path.write_text(
        "2024-01-02,Purchase at Store,100.00\n"
        "2024-01-03,Refund,-20.00\n",
        encoding="utf-8",
    )

    # Fake profile with csv_format mapping
    profile = {
        "bank_name": "My Card",
        "source_type": "credit_card",
        "csv_format": {
            "columns": {
                "transaction_date": 0,
                "description": 1,
                "amount": 2,
            },
            "date_format": "YYYY-MM-DD",
            "skip_footer_rows": False,
        },
    }

    txs = parse_csv(csv_path, profile)
    assert len(txs) == 2

    for tx in txs:
        _assert_canonical_shape(tx, source_expected="credit_card")
        assert tx["Date"] in ("2024-01-02", "2024-01-03")

    # First row: amount = 100.00 -> Debit
    assert txs[0]["Debit"] == 100.0
    assert txs[0]["Credit"] == 0.0

    # Second row: amount = -20.00 -> Credit
    assert txs[1]["Debit"] == 0.0
    assert txs[1]["Credit"] == 20.0
