# **Rule Generator Constraints**  
### _Authoritative Design & Behavior Contract for the Rule Generator Wizard_  
**Version:** 1.0.0  
**Status:** Stable  
**Owner:** Hector Rivero  
**Last Updated:** _2026‑01‑31_

---

## **0. Purpose**

This document defines the **non‑negotiable architectural constraints**, **behavioral invariants**, and **anti‑goals** governing the Rule Generator Wizard.  
It ensures that all human contributors and Copilot Agents operate within a stable, predictable, and auditable framework.

This document is **authoritative**.  
Agents must reference it, not reinterpret it.

---

## **1. Immutable Design Decisions**

### **1.1 Rules Are Pure Data**
- Rules are JSON objects only.  
- No embedded logic, expressions, or dynamic code.  
- The engine interprets rules; the Wizard only writes them.

### **1.2 Wizard Writes Rules, Engine Executes Rules**
- Wizard responsibilities:
  - Collect user intent  
  - Produce rule JSON  
  - Validate against schema  
  - Save to correct config  
- Wizard does **not** classify transactions.

### **1.3 Deterministic Behavior**
- No randomness or heuristics.  
- Pattern matching must be explicit and reproducible.

### **1.4 Explicit Priority Resolution**
- Priority is a required, explicit field.  
- No implicit ordering or silent overrides.

### **1.5 Separation of Concerns**
- Wizard UI/CLI contains no business logic.  
- Business logic lives in:
  - Rule schema  
  - Validation engine  
  - Pattern suggestion engine  

### **1.6 Schema Is Law**
- JSON schema defines:
  - Allowed fields  
  - Types  
  - Required vs optional  
  - Validation rules  
- Agents must **import**, not redesign, the schema.

---

## **2. Invariants**

### **2.1 No Partial Matches**
A rule either matches fully or not at all.  
Partial matches must be surfaced as warnings or errors.

### **2.2 Every Rule Declares Scope**
Scope must be:
- `"bank"`  
- `"global"`

No implicit scoping.

### **2.3 Evaluation Order Must Be Inspectable**
The engine must expose:
- Final priority ordering  
- Conflicts  
- Overrides  

Wizard must warn on conflicts.

### **2.4 Strict Validation**
A rule cannot be saved if:
- It violates schema  
- It produces false positives  
- It produces zero matches when examples were provided  

Dry‑run mode must show:
- Matches  
- False positives  
- False negatives  

### **2.5 No Silent Behavior**
No silent:
- Normalization  
- Fallbacks  
- Field inference  

### **2.6 Human‑Readable Output**
Rule JSON must be formatted and readable.

---

## **3. Anti‑Goals**

### **3.1 No Machine Learning**
No fuzzy matching, embeddings, or probabilistic suggestions.

### **3.2 No Auto‑Classification**
Wizard does not classify transactions.

### **3.3 No Hidden Overrides**
No implicit catch‑alls or auto‑generated rules.

### **3.4 No Schema Mutation**
Schema changes require human review.

### **3.5 No Multi‑Step Agent Autonomy**
Agents must not:
- Create modules unless instructed  
- Modify unrelated files  
- Infer architecture  
- Perform multi‑unit tasks  

### **3.6 No Wizard Logic Inside Engine**
Engine and Wizard remain decoupled.

---

## **4. Required Interfaces**

### **4.1 Wizard → Engine Contract**

```json
{
  "id": "string",
  "scope": "bank | global",
  "priority": 0,
  "match": { },
  "action": { },
  "examples": [ ]
}
```

### **4.2 Validation Contract**

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

### **4.3 Test Harness Contract**
A normalized transaction (used by the classifier and pipeline) MUST have the canonical shape produced by [`normalize_tx_to_canonical_shape`](src/utils.py):

- `Date` — string in ISO format "YYYY-MM-DD" or null
- `Description` — non-empty string
- `Debit` — float >= 0.0 (money out / expense)
- `Credit` — float >= 0.0 (money in / income)
- `Balance` — float or null
- `source` — string tag identifying origin (e.g., `"bank_account"`, `"credit_card"`, profile id or filename)
- `raw_fields` — optional dict with original parsed fields (e.g., `transaction_date`, `amount`, `posting_date`)

Example:
```json
{
  "Date": "2024-01-02",
  "Description": "THE HOME DEPOT",
  "Debit": 100.0,
  "Credit": 0.0,
  "Balance": null,
  "source": "td_visa",
  "raw_fields": {"transaction_date": "01/02", "amount": "100.00"}
}

---

## **5. Constraints for Agent Work Units**

Agents must follow:

- Single responsibility  
- Explicit inputs/outputs  
- No architectural inference  
- No schema changes  
- No cross‑module edits unless specified  
- Must reference:
  - This constraints document  
  - The rule schema  
  - The evaluation contract  

---

## **6. Versioning & Change Control**

Changes to:
- Schema  
- Invariants  
- Priority rules  
- Validation semantics  

require:
- Human review  
- Updated constraints document  
- Updated test harness  
- Updated Wizard logic  

Agents cannot initiate these changes.

---

## **7. Git / GitHub workflow**

Keep process documentation separate from product constraints. See the canonical workflow document:

`docs/github_agent_workflow.md`

Rationale: constraints describe feature behavior; workflow describes process and collaboration. Agent Briefs should reference both documents.

---

## **8. Status**

This document is authoritative.  
All future work on the Rule Generator Wizard must comply with it.
