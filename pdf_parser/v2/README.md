# Statement Parser — v2 (Experimental / Modular Pipeline)

## Status
**ACTIVE — v2 modular experimentation layer**

v2 is a **sandbox / evolution layer** used to explore:
- alternative parsers
- layout detectors
- rule engines
- normalization strategies

v2 is **NOT production-locked** and is **NOT coupled** to v1.

---

## Purpose of v2

v2 exists to experiment with and validate:
- different parsing strategies per bank
- multiple layout detectors per bank
- rule engines for fixing edge cases
- normalization pipelines

v2 helps answer:
- *What parsing strategy works best?*
- *Which layout detector is reliable?*
- *Which rules are reusable across banks?*

---

## High-Level Architecture

PDF
├── Text Extraction
├── Classification
├── Layout Detection
├── Bank-Specific Parsers
├── Rule Engine
├── Normalization
└── Logging



Each step is **modular and replaceable**.

---

## Folder Structure (v2)

pdf_parser/v2/
├── classifier/
│ └── classifier.py
│
├── extractor/
│ └── pdf_text_extractor.py
│
├── layout_detector/
│ ├── sbi_layout_detector.py
│ └── union_layout_detector.py
│
├── parsers/
│ ├── sbi/
│ │ ├── parser_table_v1.py
│ │ └── parser_table_v2.py
│ │
│ ├── union/
│ │ ├── parser_table_v1.py
│ │ └── parser_table_v2.py
│ │
│ ├── hdfc/
│ │ └── parser_table.py
│ │
│ └── icici/
│ └── parser_table.py
│
├── rule_engine/
│ ├── fix_hdfc_direction.py
│ ├── fix_icici_direction.py
│ └── normalize_transaction.py
│
├── utils/
│ └── logger.py
│
├── logs/
│ └── statement_parser.jsonl
│
└── test.py



---

## Module Responsibilities

### 1️⃣ `classifier/`
- Identifies document type
- Attempts bank identification
- Produces confidence + signals
- **Advisory only**

---

### 2️⃣ `extractor/`
- Extracts raw text from PDF
- No parsing, no logic
- Used by classifier and layout detectors

---

### 3️⃣ `layout_detector/`
- Bank-specific layout detection
- Determines **how** the document is structured
- Examples:
  - `SBI_V1`, `SBI_V2`
  - `UNION_TABLE`
- Experimental — multiple detectors allowed

---

### 4️⃣ `parsers/`
- Bank-specific parsing logic
- Multiple versions allowed per bank
- Used to compare approaches

Examples:
- `parser_table_v1.py`
- `parser_table_v2.py`

No shared base enforced in v2.

---

### 5️⃣ `rule_engine/`
- Post-parse corrections
- Direction fixes (debit / credit)
- Normalization helpers
- Used to clean parser output

Rules are:
- composable
- optional
- order-dependent

---

### 6️⃣ `utils/logger.py`
- Experimental logging
- v2-only logs
- Not shared with v1 logging

---

### 7️⃣ `logs/`
- Stores experimental outputs
- JSON / JSONL
- Not considered stable artifacts

---

### 8️⃣ `test.py`
- Manual test runner
- Used for quick validation
- No automated test guarantees

---

## Relationship to v1

| Aspect | v1 | v2 |
|----|----|----|
| Stability | Stable / frozen | Experimental |
| Parsing | Final | Iterative |
| Logging | Structured | Exploratory |
| Architecture | Strict | Flexible |

**Rules:**
- v2 may inspire v1
- v1 must not depend on v2
- No shared imports from v2 → v1

---

## What v2 Is Allowed to Break

- APIs
- folder structure
- parser outputs
- logging formats

This is intentional.

---

## What v2 Is NOT Allowed to Do

- ❌ Replace v1
- ❌ Modify v1 at runtime
- ❌ Be used in production paths
- ❌ Create tight coupling

---

## Intended Future Use

v2 outputs will be used to:
- choose best parsing strategy
- migrate proven logic into v1
- design v3 orchestration layer

---

## Summary

- **v1 = production-grade parser**
- **v2 = research & experimentation**
- Separation is deliberate and permanent

