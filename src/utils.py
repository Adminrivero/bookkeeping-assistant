import os
import sys
import json
import time
import logging
import jsonschema
from pathlib import Path
from typing import Any, Dict, Callable
from functools import wraps

def _auto_detect_debug() -> bool:
    """Auto-detect debug mode via environment or attached debugger."""
    if os.getenv("VSCODE_DEBUGGING") == "1":
        return True
    return sys.gettrace() is not None

# Global flags
use_logging = False  # toggled by CLI
debug_mode = _auto_detect_debug()
perf_monitoring = True  # toggled as needed


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
        try:
            print(message)
        except UnicodeEncodeError:
            # Fallback: write bytes to stdout.buffer encoded as utf-8
            try:
                # ensure a newline too
                sys.stdout.buffer.write((message + "\n").encode("utf-8"))
                sys.stdout.buffer.flush()
            except Exception:
                # Last-resort fallback: print ASCII with replacement to avoid raising
                print(message.encode("ascii", errors="replace").decode("ascii"))


def time_it(fn: Callable) -> Callable:
    """
    Decorator to time function execution and log duration.
    Only outputs if perf_monitoring is enabled.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # If monitoring is OFF, just call the function
        if not perf_monitoring:
            return fn(*args, **kwargs)
        
        start_time = time.perf_counter()
        result = fn(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        notify(f"PERF: Function '{fn.__name__}' took {duration:.6f}s", level="info")
        return result
    return wrapper


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
    Supports fuzzy matching: if exact bank.json not found, searches for partial matches.
    
    Args:
        bank: Bank identifier (e.g., "td", "TD Visa", "triangle")
        profiles_dir: Directory containing <bank>.json and profile_template.json
        schema_filename: Name of the JSON schema file
    
    Returns:
        Dict[str, Any]: Validated bank profile config
    
    Raises:
        FileNotFoundError: If no profile found (exact or partial match)
    """
    profiles_dir = Path(profiles_dir)
    schema_path = profiles_dir / schema_filename

    if not schema_path.exists():
        raise FileNotFoundError(f"No profile schema found at: {schema_path}")

    # --- Try exact match first ---
    profile_path = profiles_dir / f"{bank}.json"
    if profile_path.exists():
        with open(profile_path, "r") as f:
            profile = json.load(f)
        with open(schema_path, "r") as f:
            schema = json.load(f)
        jsonschema.validate(profile, schema)
        return profile

    # --- Fuzzy match: search for files containing the bank id (case-insensitive) ---
    bank_lower = bank.lower()
    matching_files = [
        f for f in profiles_dir.glob("*.json")
        if f.name != schema_filename and bank_lower in f.stem.lower()
    ]

    if matching_files:
        # Use the first match (or pick the best one if multiple)
        profile_path = matching_files[0]
        notify(f"No exact profile found for bank '{bank}'. Using closest match: '{profile_path.stem}'.", level="info")
        with open(profile_path, "r") as f:
            profile = json.load(f)
        with open(schema_path, "r") as f:
            schema = json.load(f)
        jsonschema.validate(profile, schema)
        return profile

    # --- No match found ---
    available = [f.stem for f in profiles_dir.glob("*.json") if f.name != schema_filename]
    raise FileNotFoundError(f"No profile found for bank '{bank}'. Available profiles: {', '.join(available)}")