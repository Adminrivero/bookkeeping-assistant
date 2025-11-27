import sys
import json
import pytest
import project
import subprocess
from pathlib import Path

# --- Fixtures ---

@pytest.fixture
def fake_cli_data(tmp_path):
    """Prepare fake data directories for smoke test."""
    year_dir = tmp_path / "data" / "2025"
    year_dir.mkdir(parents=True)

    # Root account CSV
    (year_dir / "account.csv").write_text("2025-01-01,Deposit,100.00")

    # Triangle bank CSV
    triangle_dir = year_dir / "triangle"
    triangle_dir.mkdir()
    (triangle_dir / "triangle_may.csv").write_text("05/01/2025,Merchant,50.00,,950.00")

    # CIBC bank PDF (fake content)
    cibc_dir = year_dir / "cibc"
    cibc_dir.mkdir()
    (cibc_dir / "cibc_may.pdf").write_text("%PDF-1.4 fake content")

    return tmp_path

# --- Tests ---

def test_cli_smoke(fake_cli_data, monkeypatch):
    # Change working directory to tmp_path so CLI sees fake data
    monkeypatch.chdir(fake_cli_data)

    # Run CLI with year and banks
    result = subprocess.run(
        [sys.executable, "project.py", "-y", "2025", "-b", "triangle", "cibc"],
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
