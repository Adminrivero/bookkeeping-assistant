import pytest
import json
from pathlib import Path
from src.utils import load_rules, load_bank_profile, setup_paths

def test_load_rules(tmp_path):
    rules = {"_rules": []}
    f = tmp_path / "rules.json"
    f.write_text(json.dumps(rules))
    assert load_rules(f) == rules

def test_load_bank_profile(tmp_path):
    profiles_dir = tmp_path / "bank_profiles"
    profiles_dir.mkdir()
    profile = {"bank_name": "sample"}
    (profiles_dir / "sample.json").write_text(json.dumps(profile))
    (profiles_dir / "profile_template.json").write_text(json.dumps({"type": "object"}))
    loaded = load_bank_profile("sample", profiles_dir=profiles_dir)
    assert loaded["bank_name"] == "sample"

def test_setup_paths_success(tmp_path):
    year_dir = tmp_path / "2025"
    year_dir.mkdir()
    csv_file = year_dir / "account.csv"
    csv_file.write_text("2025-01-01,Deposit,100.00")

    input_dir, output_dir, input_files = setup_paths(2025)
    assert input_dir.exists()
    assert output_dir.exists()
    assert csv_file in input_files

def test_setup_paths_no_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        setup_paths(2099)

def test_setup_paths_no_csv(tmp_path):
    year_dir = tmp_path / "2025"
    year_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        setup_paths(2025)