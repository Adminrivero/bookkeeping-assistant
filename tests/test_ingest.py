import pytest
import os
from src import ingest

# --------------------------
# Fixtures: create fake CSVs
# --------------------------

@pytest.fixture
def simple_ledger_csv(tmp_path):
    """No headers, fixed column order: Date, Description, Debit, Credit, Balance"""
    content = """2025-10-31,ONLINE TRANSFER,1500.00,,200.00
2025-11-01,ATM WITHDRAWAL,100.00,,100.00
2025-11-02,E-TRANSFER,,250.00,350.00
"""
    path = tmp_path / "simple.csv"
    path.write_text(content)
    return str(path)

@pytest.fixture
def headered_csv(tmp_path):
    """With headers, separate Debit/Credit columns"""
    content = """Date,Description,Debit,Credit,Balance
2025-10-31,ONLINE TRANSFER,1500.00,,200.00
2025-11-01,ATM WITHDRAWAL,100.00,,100.00
2025-11-02,E-TRANSFER,,250.00,350.00
"""
    path = tmp_path / "headered.csv"
    path.write_text(content)
    return str(path)

@pytest.fixture
def headered_amount_csv(tmp_path):
    """With headers, single Amount column (positive=credit, negative=debit)"""
    content = """Date,Description,Amount,Balance
2025-10-31,ONLINE TRANSFER,-1500.00,200.00
2025-11-01,ATM WITHDRAWAL,-100.00,100.00
2025-11-02,E-TRANSFER,250.00,350.00
"""
    path = tmp_path / "amount.csv"
    path.write_text(content)
    return str(path)

# --------------------------
# Tests
# --------------------------

def test_simple_ledger_ingestion(simple_ledger_csv):
    txs = ingest.load_csv(simple_ledger_csv)
    assert len(txs) == 3
    assert txs[0]["Date"] == "2025-10-31"
    assert txs[0]["Description"] == "ONLINE TRANSFER"
    assert txs[0]["Debit"] == 1500.00
    assert txs[2]["Credit"] == 250.00

def test_headered_ingestion(headered_csv):
    txs = ingest.load_csv(headered_csv)
    assert len(txs) == 3
    assert txs[1]["Description"] == "ATM WITHDRAWAL"
    assert txs[1]["Debit"] == 100.00
    assert txs[2]["Credit"] == 250.00

def test_headered_amount_ingestion(headered_amount_csv):
    txs = ingest.load_csv(headered_amount_csv)
    assert len(txs) == 3
    # Negative amounts → Debit
    assert txs[0]["Debit"] == 1500.00
    # Positive amounts → Credit
    assert txs[2]["Credit"] == 250.00
    