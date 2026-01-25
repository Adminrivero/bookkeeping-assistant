import sys
import json
import argparse
import pytest
from pathlib import Path
import project

# --------------------------
# Tests for get_cli_args
# --------------------------
def test_get_cli_args_defaults(monkeypatch):
    """Ensure defaults are applied when no args provided."""
    monkeypatch.setattr(sys, 'argv', ['project.py'])
    args = project.get_cli_args()
    assert isinstance(args, argparse.Namespace)
    assert args.year is not None
    assert args.rules == Path('config/allocation_rules.json')

def test_get_cli_args_with_flags(monkeypatch, tmp_path):
    """Ensure CLI flags are parsed correctly and override defaults."""
    rules_file = tmp_path / "custom_rules.json"
    rules_file.write_text('{}')  # Create an empty JSON file for testing
    monkeypatch.setattr(
        sys, 'argv', ['project.py', '--year', '2023', '--rules', str(rules_file)]
    )
    args = project.get_cli_args()
    assert args.year == 2023
    assert args.rules == rules_file

# --------------------------
# Tests for setup_paths
# --------------------------
def test_setup_paths(monkeypatch, tmp_path):
    """Ensure setup_paths validates input dir and creates output dir."""
    year = 2024
    input_dir = tmp_path / "data" / str(year)
    input_dir.mkdir(parents=True)
    csv_file = input_dir / "transactions.csv"
    csv_file.write_text("2024-01-01,Test,100,,200")

    # Patch Path to point to tmp_path
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.chdir(tmp_path)

    in_dir, out_dir, files = project.setup_paths(year)
    assert in_dir.exists()
    assert out_dir.exists()
    assert files[0].name == "transactions.csv"

    monkeypatch.undo()

def test_setup_paths_missing_dir(tmp_path):
    """Ensure FileNotFoundError is raised if input dir missing."""
    with pytest.raises(FileNotFoundError):
        project.setup_paths(2099)

def test_setup_paths_no_csv(tmp_path):
    """Ensure FileNotFoundError is raised if no CSV files found."""
    year = 2023
    input_dir = tmp_path / "data" / str(year)
    input_dir.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        project.setup_paths(year)

# --------------------------
# Tests for load_rules
# --------------------------

def test_load_rules_valid(tmp_path):
    """Ensure valid JSON rules file loads correctly."""
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps({"_rules": []}))
    rules = project.load_rules(rules_file)
    assert isinstance(rules, dict)
    assert "_rules" in rules

def test_load_rules_missing(tmp_path):
    """Ensure FileNotFoundError is raised if rules file missing."""
    rules_file = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        project.load_rules(rules_file)

def test_load_rules_invalid_json(tmp_path):
    """Ensure JSONDecodeError is raised if file is invalid JSON."""
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("{ invalid json }")
    with pytest.raises(json.JSONDecodeError):
        project.load_rules(rules_file)

def test_load_rules_not_dict(tmp_path):
    """Ensure TypeError is raised if JSON is not a dict."""
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(TypeError):
        project.load_rules(rules_file)