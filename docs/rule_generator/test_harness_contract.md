# ✅ **2.3 — Test Harness Contract (`test_harness_contract.md`)**
## **Test Harness Contract**  
**Version:** 1.0.0  
**Status:** Stable  
**Owner:** Hector Rivero  
**Last Updated:** _2026‑01‑31_

---

### **1. Purpose**

Defines the canonical transaction shape and match-report semantics used by:

- Rule validation engine  
- Rule Generator Wizard  
- Unit tests  
- Classification engine  

---

## **2. Canonical Transaction Shape**

A normalized transaction MUST match the output of  
`normalize_tx_to_canonical_shape` in `src/utils.py`.

### **Required fields**

- `Date` — ISO `"YYYY-MM-DD"` or null  
- `Description` — non-empty string  
- `Debit` — float ≥ 0.0  
- `Credit` — float ≥ 0.0  
- `Balance` — float or null  
- `source` — string identifying origin (e.g., `"td_visa"`)  

### **Optional fields**

- `raw_fields` — dict of original parsed fields  

### **Example**

```json
{
  "Date": "2024-01-02",
  "Description": "THE HOME DEPOT",
  "Debit": 100.0,
  "Credit": 0.0,
  "Balance": null,
  "source": "td_visa",
  "raw_fields": {
    "transaction_date": "01/02",
    "amount": "100.00"
  }
}
```

---

## **3. Match Report Semantics**

The validation engine must produce:

- `matches` — transactions that satisfy all match conditions  
- `false_positives` — matched but should not have  
- `false_negatives` — did not match but should have  
