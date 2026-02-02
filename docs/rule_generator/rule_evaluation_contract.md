# **Rule Evaluation Contract (Legacy-Compatible v1)**  
**Version:** 1.0.0  
**Status:** Stable  
**Owner:** Hector Rivero  
**Last Updated:** 2026‑01‑31

---

## **1. Purpose**

This document defines the contract between:

- The **Rule Generator Wizard** (producer of rule blocks)  
- The **Legacy Classification Engine** (consumer of rule blocks)  
- The **Validation Engine** (tester of rule blocks)  

The Wizard must generate rules that are **100% compatible** with the existing `allocation_rules.json` structure.

---

## **2. Rule Structure**

A rule block consists of:

- Optional Wizard metadata:
  - `rule_id`
  - `priority`
  - `scope`
- Required legacy fields:
  - `category_name`
  - `transaction_type`
  - `logic`
  - `rules` (DSL)
  - `dual_entry` (optional depending on transaction type)

Example:

```json
{
  "rule_id": "office_expenses_home_depot",
  "priority": 10,
  "scope": "global",

  "category_name": "Office Expenses - Retail/Hardware",
  "transaction_type": "EXPENSE",
  "logic": "MUST_MATCH_ANY",
  "rules": [
    { "field": "Description", "operator": "CONTAINS", "value": "THE HOME DEPOT" }
  ],
  "dual_entry": {
    "DR_COLUMN": { "name": "Office Expenses", "letter": "I" },
    "CR_COLUMN": { "name": "Shareholder Contribution (CR)", "letter": "F" },
    "APPLY_PERCENTAGE": 1.0
  }
}
```

---

## **3. Match Semantics (Legacy DSL)**

### **3.1 Top-Level Logic**
`logic` determines how the top-level `rules` array is evaluated:

- `MUST_MATCH_ANY` → OR  
- `MUST_MATCH_ALL` → AND  

### **3.2 Rule Objects**
A rule is either:

#### **A. Simple rule**
```json
{ "field": "Description", "operator": "CONTAINS", "value": "FIDO" }
```

#### **B. Group rule**
```json
{
  "group_logic": "MUST_MATCH_ANY",
  "rules": [ ... ]
}
```

Group rules allow nested AND/OR logic.

### **3.3 Operators**
Supported operators:

- `CONTAINS`  
- `STARTS_WITH`  
- `EQUALS`  
- `BETWEEN` (value = `[min, max]`)  
- `LESS_THAN_OR_EQUAL_TO`  

### **3.4 Field Semantics**
Fields refer to canonical transaction fields:

- `Description`  
- `Debit`  
- `Credit`  
- `Date`  
- `Balance`  

---

## **4. Action Semantics**

Action is defined by:

- `category_name`  
- `transaction_type`  
- `dual_entry` bookkeeping output  

The engine uses these fields exactly as-is.

---

## **5. Priority & Scope (Wizard Metadata)**

These fields are **optional** and ignored by the legacy engine:

- `priority` — Wizard uses this to order rules before writing  
- `scope` — Wizard uses this to filter rules by bank profile  
- `rule_id` — Wizard uses this for identification and conflict detection  

The engine still evaluates rules **in file order**.

---

## **6. Validation Contract**

The validation engine must output:

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "match_report": {
    "matches": [],
    "false_positives": [],
    "false_negatives": []
  }
}
```

### **6.1 Errors**
- Schema violations  
- Invalid operator/value combinations  
- Impossible ranges  
- Zero matches when examples provided  
- Conflicting Wizard metadata (duplicate `rule_id`, duplicate `priority`)  

### **6.2 Warnings**
- Very broad match conditions  
- Overlapping rules  
- Rules that match many transactions  

---

## **7. Engine Contract**

The legacy engine must:

- Load `_rules` in file order  
- Evaluate DSL deterministically  
- Apply dual-entry bookkeeping  

The engine must **ignore**:

- `rule_id`  
- `priority`  
- `scope`  
