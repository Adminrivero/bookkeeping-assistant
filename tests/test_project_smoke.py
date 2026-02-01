import sys
import json
import pytest
import project
import subprocess
from pathlib import Path
from src import pdf_ingest, csv_ingest

# --- Fixtures ---

@pytest.fixture
def fake_cli_data(tmp_path):
    """Prepare fake data directories for smoke test and minimal config profiles."""
    year_dir = tmp_path / "data" / "2025"
    year_dir.mkdir(parents=True)

    # Root account CSV
    (year_dir / "account.csv").write_text("2025-01-01,Deposit,100.00")

    # Triangle bank PDF (fake content)
    triangle_dir = year_dir / "triangle"
    triangle_dir.mkdir()
    (triangle_dir / "triangle_may.pdf").write_text("%PDF-1.4 fake content")

    # CIBC bank PDF (fake content)
    cibc_dir = year_dir / "cibc"
    cibc_dir.mkdir()
    (cibc_dir / "cibc_may.pdf").write_text("%PDF-1.4 fake content")
    
    # TD Visa bank CSV (fake content)
    td_visa_dir = year_dir / "td_visa"
    td_visa_dir.mkdir()
    (td_visa_dir / "td_visa_may.csv").write_text("05/01/2025,Merchant,50.00,,950.00")

    # Create a minimal config with allocation_rules.json so CLI can discover rules
    config_dir = tmp_path / "config"
    bank_profiles_dir = config_dir / "bank_profiles"
    bank_profiles_dir.mkdir(parents=True, exist_ok=True)

    (config_dir / "allocation_rules.json").write_text(json.dumps({"_rules": []}))

    # Minimal schema used by load_bank_profile validation
    profile_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "bank_name": {"type": "string"},
            "parser": {"type": "string"},
            "formats": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["bank_name"]
    }
    (bank_profiles_dir / "bank_profile_schema.json").write_text(json.dumps(profile_schema))

    # Minimal per-bank profiles required by pipeline (include 'formats' so pipeline accepts CSV/PDF)
    (bank_profiles_dir / "triangle.json").write_text(json.dumps({
        "bank_name": "triangle",
        "parser": "pdf",
        "formats": ["pdf"]
    }))
    (bank_profiles_dir / "cibc.json").write_text(json.dumps({
        "bank_name": "cibc",
        "parser": "pdf",
        "formats": ["pdf"]
    }))
    (bank_profiles_dir / "td_visa.json").write_text(json.dumps({
        "bank_name": "td_visa",
        "parser": "csv",
        "formats": ["csv"]
    }))

    return tmp_path

# --- Tests ---

def test_cli_smoke(fake_cli_data, monkeypatch):
    # Change working directory to tmp_path so CLI sees fake data
    monkeypatch.chdir(fake_cli_data)
    
    # Avoid real PDF parsing; stub it so CLI proceeds
    monkeypatch.setattr(pdf_ingest, "parse_pdf", lambda f, p: [])
    # For safety, stub csv parsing to a minimal transaction
    monkeypatch.setattr(csv_ingest, "parse_csv", lambda f, p: [
        {"transaction_date": "2025-05-01", "description": "CSV Tx", "amount": 50.00, "balance": 950.00, "source": "Triangle", "section": "Transactions"}
    ])
    
    # Path to the project.py file
    project_file = Path(__file__).resolve().parent.parent / "project.py"

    # Run CLI with year and banks
    result = subprocess.run(
        [sys.executable, str(project_file), "-y", "2025", "-b", "triangle", "cibc"],
        capture_output=True, text=True
    )

    # CLI should exit cleanly
    assert result.returncode == 0
    # Output should mention success
    assert "Success! Pipeline complete" in result.stdout

def test_main_smoke(tmp_path, monkeypatch):
    """
    End-to-end smoke test for project.main().
    Creates a fake data/{year} with one CSV and a fake rules file,
    then runs main() with CLI args.
    """
    year = 2024

    # --- Setup fake environment ---
    data_dir = tmp_path / "data" / str(year)
    data_dir.mkdir(parents=True)
    csv_file = data_dir / "transactions.csv"
    csv_file.write_text("2024-01-01,Test Transaction,100,,200")

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    rules_file = config_dir / "allocation_rules.json"
    rules_file.write_text(json.dumps({"_rules": []}))

    # --- Patch working directory and CLI args ---
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["project.py", "--year", str(year), "--rules", str(rules_file)])

    # --- Run main() ---
    project.main()

    # --- Verify output workbook exists ---
    output_file = tmp_path / "output" / str(year) / f"bookkeeping_{year}.xlsx"
    assert output_file.exists()
