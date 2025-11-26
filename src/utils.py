import logging
import json
import jsonschema
from pathlib import Path
from typing import Any, Dict

use_logging = False  # global flag, toggled by CLI

def notify(message: str, level: str = "info"):
    """
    Unified output helper.
    - By default, prints to stdout.
    - If logging is enabled, uses Python's logging module.
    """
    if use_logging:
        log_fn = getattr(logging, level, logging.info)
        log_fn(message)
    else:
        print(message)


def setup_paths(year: int, base_dir: Path = Path("data")) -> tuple[Path, Path, list[Path]]:
    """
    Validate input directory, find root CSVs, and create output directory.

    Args:
        year (int): Tax year
        base_dir (Path): Base data directory

    Returns:
        (input_dir, output_dir, input_files)
    """
    input_dir = base_dir / str(year)
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    output_dir = Path("output") / str(year)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find CSV files inside the year's input directory (top-level only)
    files = [p for p in input_dir.glob("*.csv") if p.is_file()]
    if not files:
        # If no CSVs found in the year folder, raise FileNotFoundError 
        raise FileNotFoundError(f"No CSV files found in input directory: {input_dir}")

    return input_dir, output_dir, files


def load_rules(rules_path: Path) -> Dict[str, Any]:
    """Load and validate the JSON allocation rules file."""
    if not Path(rules_path).is_file():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    with open(rules_path, "r") as f:
        rules = json.load(f)
    if not isinstance(rules, dict) or "_rules" not in rules:
        raise TypeError(f"Rules file {rules_path} does not contain a valid JSON object or missing '_rules' key.")
    return rules


def load_bank_profile(bank: str, profiles_dir: Path = Path("config/bank_profiles"), schema_filename: str = "profile_template.json") -> Dict[str, Any]:
    """
    Load and validate a per-bank profile config.
    - profiles_dir: directory containing <bank>.json and profile_template.json
    """
    profile_path = Path(profiles_dir) / f"{bank}.json"
    schema_path = Path(profiles_dir) / schema_filename

    if not profile_path.exists():
        raise FileNotFoundError(f"No profile config found for bank: {bank}")
    if not schema_path.exists():
        raise FileNotFoundError(f"No profile schema found at: {schema_path}")

    with open(profile_path, "r") as f:
        profile = json.load(f)
    with open(schema_path, "r") as f:
        schema = json.load(f)
    jsonschema.validate(instance=profile, schema=schema)
    return profile