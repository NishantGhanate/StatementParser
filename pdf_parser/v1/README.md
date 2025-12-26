# Statement Parser — v1 (Core Stable)

## Status
**FROZEN — v1.0-parser-core-stable**

The parsing core is stable and locked.  
Supported banks are parsed with deterministic routing and no heuristic guessing.

---

## Architecture Overview

The system is split into **four strict layers**:

PDF
├── Text Extraction
│
├── Layout Detection (HOW the document is structured)
│
├── Bank Routing (layout > bank, locked)
│
└── Bank Parsers (bank-specific logic only)



**Key principle:**  
👉 **Layout decides routing, not bank name.**

---

## Folder Structure

pdf_parser/v1/
├── banks/
│ ├── sbi.py
│ ├── hdfc.py
│ ├── union/
│ │ ├── union_table.py
│ │ └── union_text.py
│ └── icici.py
│
├── rules/
│ ├── base.py
│ ├── sbi_rules.py
│ └── icici_rules.py
│
├── core/
│ ├── parser.py # orchestrator (routing only)
│ ├── table_extractor.py
│ └── transaction_builder.py
│
├── detector/
│ ├── bank_detector.py # identification only
│ └── layout_detector.py # routing signal (critical)
│
├── logging/
│ └── parser_logger.py
│
└── tests/
└── (manual / smoke tests only)




---

## Routing Priority (LOCKED)

Routing order inside `core/parser.py` is **non-negotiable**:

1. **UNION_TABLE**
2. **UNION_TEXT**
3. **ICICI_TABLE**
4. **HDFC_TEXT**
5. **SBI_V1**
6. Hard fail (no guessing)

This prevents:
- SBI false positives inside UNION / ICICI
- Keyword collisions (UPI refs, IFSC noise)

---

## Supported Banks & Layouts

| Bank  | Layout        | Route Type | Status |
|------|--------------|-----------|--------|
| SBI  | SBI_V1        | Table     | ✅ Stable |
| HDFC | HDFC_TEXT     | Text      | ✅ Stable (exception) |
| UNION| UNION_TABLE   | Table     | ✅ Stable |
| UNION| UNION_TEXT    | Text      | ✅ Stable |
| ICICI| ICICI_TABLE   | Table     | ✅ Stable |

---

## Known Exceptions (By Design)

### HDFC
- `pdfplumber.extract_tables()` unreliable
- Debit / Credit derived from **balance delta**
- Explicit text-based exception

### UNION_TEXT
- Non-tabular PDF
- Amount pattern: `<amount> (Dr|Cr) <balance> (Cr)`
- Description extracted from nearest preceding text line
- No OCR, no heuristics

---

## What Is Explicitly NOT Allowed

- ❌ Guessing transaction type
- ❌ Fallback routing
- ❌ Mixing parsing logic into `core/parser.py`
- ❌ Bank rules outside `rules/`
- ❌ Multiple files named `parser.py`

---

## Logging (FROZEN)

### Log Format
Structured JSON, one line per event:

```json
{
  "ts": "ISO-8601",
  "stage": "detect | result",
  "detected_bank": "...",
  "detected_layout": "...",
  "bank": "...",
  "layout": "...",
  "count": 115
}
