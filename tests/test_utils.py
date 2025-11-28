import io
import sys
import json
import pytest
from typing import BinaryIO
from pathlib import Path
from src.utils import load_rules, load_bank_profile, setup_paths, notify

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

    input_dir, output_dir, input_files = setup_paths(2025, base_dir=tmp_path)
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

def test_notify_unicode_fallback(monkeypatch):
    """
    Ensure notify doesn't raise when stdout encoding can't represent unicode characters.
    """
    # Fake stdout with cp1252 encoding (a Windows fallback)
    class FakeStdOut(io.StringIO):
        encoding = 'cp1252'
        
        def __init__(self):
            super().__init__()
            # Use a BinaryIO-backed buffer by default so the property always returns a BinaryIO
            self._buffer: BinaryIO = io.BytesIO()
        
        @property
        def buffer(self) -> BinaryIO:
            return self._buffer
        
        @buffer.setter
        def buffer(self, value: BinaryIO) -> None:
            self._buffer = value
            self._buffer = value
            
    fake_stdout = FakeStdOut()
    # Provide a buffer attribute so the fallback code can write bytes to buffer
    fake_buffer = io.BytesIO()
    fake_stdout.buffer = fake_buffer

    monkeypatch.setattr(sys, "stdout", fake_stdout)

    # Should not raise when containing a checkmark (emoji)
    notify("Test message with a checkmark ✅", level="info")

    # Assert either text was written to the string buffer or encoded bytes to fake buffer
    str_content = fake_stdout.getvalue()
    bytes_content = fake_buffer.getvalue()

    assert "Test message" in str_content or b"Test message" in bytes_content