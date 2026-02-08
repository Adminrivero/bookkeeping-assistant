"""Safe, deterministic I/O for allocation_rules.json."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional

from .schema import ValidationResult, validate_rules_document

DEFAULT_RULES_PATH = Path("config") / "allocation_rules.json"


def load_rules(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load rules JSON from disk, preserving key order."""

    rules_path = Path(path) if path else DEFAULT_RULES_PATH
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    return json.loads(rules_path.read_text(encoding="utf-8"))


def _atomic_write_json(target: Path, content: Dict[str, Any]) -> None:
    """Write JSON content atomically to avoid partial writes."""

    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=str(target.parent), newline=""
    ) as tmp:
        json.dump(content, tmp, indent=2, separators=(', ', ': '))
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name
    os.replace(temp_name, target)


def save_rules(
    rules: Dict[str, Any],
    *,
    path: Optional[Path] = None,
    validate_before_save: bool = False,
    schema_path: Optional[Path] = None,
) -> Optional[ValidationResult]:
    """Save rules to disk. Optionally validate before writing."""

    rules_path = Path(path) if path else DEFAULT_RULES_PATH

    validation_result: Optional[ValidationResult] = None
    if validate_before_save:
        validation_result = validate_rules_document(rules, schema_path=schema_path)
        if not validation_result["valid"]:
            return validation_result

    _atomic_write_json(rules_path, rules)
    return validation_result
