import json
from pathlib import Path
from src.utils import load_rules, load_bank_profile

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