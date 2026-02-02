"""Utilities for loading and validating rule JSON Schema and instances."""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from jsonschema.validators import validator_for

DEFAULT_SCHEMA_PATH = Path("config") / "schemas" / "rule_schema.json"


def load_rule_schema(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the rule JSON Schema from disk (default: config/schemas/rule_schema.json)."""
    schema_path = Path(path) if path else DEFAULT_SCHEMA_PATH
    if not schema_path.exists():
        raise FileNotFoundError(f"Rule schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def get_schema_validator(schema: Dict[str, Any]) -> Any:
    """Return a Validator instance for the given schema (auto-detects draft)."""
    ValidatorClass = validator_for(schema)
    ValidatorClass.check_schema(schema)
    return ValidatorClass(schema)


def validate_instance(instance: Dict[str, Any], schema_path: Optional[Path] = None) -> None:
    """
    Validate an instance (full rules document or single rule) against the schema.
    Raises jsonschema.ValidationError on failure.
    """
    schema = load_rule_schema(schema_path)
    validator = get_schema_validator(schema)
    validator.validate(instance)


def iter_validation_errors(instance: Dict[str, Any], schema_path: Optional[Path] = None):
    """Return generator of jsonschema.ValidationError for easier reporting in tests/CI."""
    schema = load_rule_schema(schema_path)
    validator = get_schema_validator(schema)
    yield from validator.iter_errors(instance)