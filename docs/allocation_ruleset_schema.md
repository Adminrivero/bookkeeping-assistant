## 📑 JSON Ruleset Schema

The classification engine is driven by an external configuration file: `allocation_rules.json`.  
This file defines an **ordered list of rules** that are evaluated sequentially. The first matching rule is applied, ensuring priority-based classification.

### Rule Object Structure

Each rule has the following fields:

| Field              | Type    | Required | Description |
|--------------------|---------|----------|-------------|
| `category_name`    | String  | ✅ | Human-readable label for the category (e.g., "Office Expenses - Retail/Hardware"). |
| `transaction_type` | String  | ✅ | Defines the accounting action (`EXPENSE`, `INCOME`, `MANUAL_CR`, `MANUAL_DR`, `INCOME_TO_OFFSET_EXPENSE`, `IGNORE_TRANSACTION`). |
| `logic`            | String  | ✅ | Rule evaluation method: `MUST_MATCH_ANY` (OR) or `MUST_MATCH_ALL` (AND). |
| `rules`            | Array   | ✅ | List of conditions or subrules (`field`, `operator`, `value`) or nested groups. |
| `dual_entry`       | Object  | ⚠️ | Required for all except `IGNORE_TRANSACTION`. Defines DR/CR columns and `APPLY_PERCENTAGE`. |

### Condition Fields

- **`field`** → Which transaction field to check (`Description`, `Debit`, `Credit`).  
- **`operator`** → Comparison method (`CONTAINS`, `STARTS_WITH`, `EQUALS`, `BETWEEN`, etc.).  
- **`value`** → String, number, or array depending on operator.  

### Dual Entry Object

```json
"dual_entry": {
  "DR_COLUMN": {"name": "Office Expenses", "letter": "I"},
  "CR_COLUMN": {"name": "Shareholder Contribution (CR)", "letter": "F"},
  "APPLY_PERCENTAGE": 1.0
}
```

- `DR_COLUMN` → Debit side of transaction.
- `CR_COLUMN` → Credit side of transaction.
- `APPLY_PERCENTAGE` → Factor applied to the amount (1.0 = full, 0.66 = partial, -1.0 = rebate).

### Nested Groups

Rules can contain subgroups for complex logic:

```json
{
  "logic": "MUST_MATCH_ALL",
  "rules": [
    {
      "group_logic": "MUST_MATCH_ANY",
      "rules": [
        {"field": "Description", "operator": "CONTAINS", "value": "ESSO"},
        {"field": "Description", "operator": "CONTAINS", "value": "7-ELEVEN"}
      ]
    },
    {"field": "Debit", "operator": "BETWEEN", "value": [20.0, 120.0]}
  ]
}
```

This example matches ("ESSO" **OR** "7-ELEVEN") **AND** any amount between $20.0 - $120.0