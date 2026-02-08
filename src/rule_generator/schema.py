"""Schema validation helpers for rule blocks and documents."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, TypedDict
from jsonschema.validators import validator_for

DEFAULT_SCHEMA_PATH = Path("config") / "schemas" / "rule_schema.json"


class ValidationIssue(TypedDict):
    """Structured validation error information."""

    path: str
    message: str


class ValidationResult(TypedDict):
    """Structured validation result returned by the validator helpers."""

    valid: bool
    errors: List[ValidationIssue]


def load_rule_schema(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the rule JSON Schema from disk (default: config/schemas/rule_schema.json)."""
    schema_path = Path(path) if path else DEFAULT_SCHEMA_PATH
    if not schema_path.exists():
        raise FileNotFoundError(f"Rule schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _build_validator(schema: Dict[str, Any], schema_fragment: Optional[Dict[str, Any]] = None):
    """Create a jsonschema Validator.

    For validating schema fragments that reference local definitions, inline
    the root schema's $defs / definitions into the fragment so local $refs
    resolve without using the deprecated RefResolver.
    """
    ValidatorClass = validator_for(schema)
    ValidatorClass.check_schema(schema)

    if schema_fragment is None:
        return ValidatorClass(schema)

    # Inline root-level definitions into the fragment so "#/$defs/..." refs resolve
    fragment = dict(schema_fragment)
    for defs_key in ("$defs", "definitions"):
        if defs_key in schema:
            fragment.setdefault(defs_key, schema[defs_key])
    # Preserve helpful metadata for the fragment validator
    for meta_key in ("$schema", "$id"):
        if meta_key in schema:
            fragment.setdefault(meta_key, schema[meta_key])

    return ValidatorClass(fragment)


def _format_error_path(parts: Iterable[Any]) -> str:
    """Render a jsonschema error path like ['_rules', 0, 'operator'] to "/_rules/0/operator"."""

    rendered = "/" + "/".join(str(part) for part in parts)
    return rendered if rendered != "//" else "/"


def _format_error(message: str, path_parts: Iterable[Any]) -> ValidationIssue:
    return {"path": _format_error_path(path_parts), "message": message}


def iter_validation_errors(
    instance: Dict[str, Any],
    schema: Optional[Dict[str, Any]] = None,
    schema_path: Optional[Path] = None,
    schema_fragment: Optional[Dict[str, Any]] = None,
) -> Iterable[Any]:
    """Yield jsonschema.ValidationError objects for the given instance."""

    loaded_schema = schema or load_rule_schema(schema_path)
    validator = _build_validator(loaded_schema, schema_fragment=schema_fragment)
    yield from validator.iter_errors(instance)


def _collect_errors(
    instance: Dict[str, Any],
    schema: Optional[Dict[str, Any]] = None,
    schema_path: Optional[Path] = None,
    schema_fragment: Optional[Dict[str, Any]] = None,
) -> List[ValidationIssue]:
    errors: List[ValidationIssue] = []
    seen = set()

    def _walk(error):
        if error.context:
            for sub_error in error.context:
                yield from _walk(sub_error)
        yield error

    for error in iter_validation_errors(
        instance,
        schema=schema,
        schema_path=schema_path,
        schema_fragment=schema_fragment,
    ):
        for nested in _walk(error):
            key = (tuple(nested.absolute_path), nested.message)
            if key in seen:
                continue
            errors.append(_format_error(nested.message, nested.absolute_path))
            seen.add(key)
    return errors


def validate_rules_document(
    rules_document: Dict[str, Any],
    *,
    schema_path: Optional[Path] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    """Validate the entire allocation rules document against the schema."""

    errors = _collect_errors(rules_document, schema=schema, schema_path=schema_path)
    return {"valid": len(errors) == 0, "errors": errors}


def validate_rule_block(
    rule_data: Dict[str, Any],
    *,
    schema_path: Optional[Path] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    """Validate an individual rule object against the rule item schema."""

    loaded_schema = schema or load_rule_schema(schema_path)
    wrapper = {
        "_name": "tmp",
        "_version": "tmp",
        "_description": "tmp",
        "_scope": [],
        "_rules": [rule_data],
    }
    errors = _collect_errors(wrapper, schema=loaded_schema, schema_path=schema_path)

    def _strip_wrapper(issue: ValidationIssue) -> ValidationIssue:
        prefix = "/_rules/0"
        path = issue["path"]
        if path.startswith(prefix):
            new_path = path[len(prefix) :] or "/"
        else:
            new_path = path
        return {"path": new_path, "message": issue["message"]}

    remapped = [_strip_wrapper(issue) for issue in errors]
    return {"valid": len(remapped) == 0, "errors": remapped}