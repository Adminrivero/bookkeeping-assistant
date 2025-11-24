import sys
import json
import pytest
from pathlib import Path
import project


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
