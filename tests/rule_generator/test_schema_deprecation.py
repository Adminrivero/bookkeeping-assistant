import warnings
from src.rule_generator.schema import validate_rule_block, load_rule_schema

def test_no_refresolver_deprecation_on_fragment_validation():
    """Ensure validating a rule block does not emit a RefResolver deprecation warning."""
    # Minimal valid-ish rule block for fragment validation
    example_rule = {
        "category_name": "Office Expenses - Retail/Hardware",
        "transaction_type": "EXPENSE",
        "logic": "MUST_MATCH_ALL",
        "rules": [
            {"field": "Description", "operator": "CONTAINS", "value": "HOME DEPOT"}
        ],
    }

    # Capture warnings and fail if any DeprecationWarning mentions RefResolver
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        validate_rule_block(example_rule)
        messages = [str(w.message) for w in rec if issubclass(w.category, DeprecationWarning)]
    assert not any("RefResolver" in m or "refresolver" in m.lower() for m in messages), f"Found RefResolver deprecation warnings: {messages}"