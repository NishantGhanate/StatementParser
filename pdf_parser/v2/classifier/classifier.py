import re
import logging
from typing import Dict


logger = logging.getLogger("PDFClassifier")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


BANK_STATEMENT_KEYWORDS = [
    "statement of account",
    "account statement",
    "details of statement",
    "statement period",
    "statement date",
    "transaction",
    "balance(rs",
    "amount(rs",
    "withdrawal",
    "deposit",
    "rtgs",
    "neft",
    "ifsc",
]

INVOICE_KEYWORDS = [
    "invoice",
    "gst",
    "bill to",
    "invoice no",
]


BANK_RULES = {
    "SBI": {
        "keywords": ["state bank of india", "sbi", "yono"],
        "ifsc_patterns": [r"SBIN\d{7}"],
    },
    "HDFC": {
        "keywords": ["hdfc bank", "hdfc bank limited", "hdfc"],
        "ifsc_patterns": [r"HDFC\d{7}"],
    },
    "ICICI": {
        "keywords": ["icici bank", "icici"],
        "ifsc_patterns": [r"ICIC\d{7}"],
    },
    "UNION": {
        "keywords": ["union bank of india", "union bank"],
        "ifsc_patterns": [r"UBIN\d{7}"],
    },
    "KOTAK": {
        "keywords": ["kotak mahindra bank", "kotak bank", "kotak"],
        "ifsc_patterns": [r"KKBK\d{7}"],
    },
    "AXIS": {
        "keywords": ["axis bank", "axis"],
        "ifsc_patterns": [r"UTIB\d{7}"],
    },
}


def classify_document_type(text: str) -> Dict:
    t = text.lower()

    bank_score = sum(1 for k in BANK_STATEMENT_KEYWORDS if k in t)
    invoice_score = sum(1 for k in INVOICE_KEYWORDS if k in t)

    if bank_score >= 1:
        return {
            "doc_type": "bank_statement",
            "confidence": min(0.6 + bank_score * 0.1, 0.95),
        }

    if invoice_score >= 2:
        return {
            "doc_type": "invoice",
            "confidence": min(0.6 + invoice_score * 0.1, 0.95),
        }

    return {
        "doc_type": "unknown",
        "confidence": 0.3,
    }


def detect_bank(text: str) -> Dict:
    scores = {}
    t = text.lower()

    for bank, rules in BANK_RULES.items():
        score = 0
        signals = []

        for kw in rules["keywords"]:
            if kw in t:
                score += 2
                signals.append(f"keyword:{kw}")

        for pattern in rules["ifsc_patterns"]:
            if re.search(pattern, text):
                score += 3
                signals.append("ifsc_match")

        if score > 0:
            scores[bank] = {"score": score, "signals": signals}

    if not scores:
        return {
            "bank_name": None,
            "confidence": 0.0,
            "signals": [],
        }

    best_bank = max(scores, key=lambda b: scores[b]["score"])
    best_score = scores[best_bank]["score"]

    return {
        "bank_name": best_bank,
        "confidence": min(0.5 + best_score * 0.1, 0.95),
        "signals": scores[best_bank]["signals"],
    }


def classify_pdf(text: str) -> Dict:
    base = classify_document_type(text)

    if base["doc_type"] != "bank_statement":
        base["bank_name"] = None
        return base

    bank_result = detect_bank(text)
    base.update(bank_result)

    return base
