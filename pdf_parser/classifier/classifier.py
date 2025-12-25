import re
import logging
from typing import Dict

# -------------------------------------------------
# LOGGING CONFIGURATION
# -------------------------------------------------
logger = logging.getLogger("PDFClassifier")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(levelname)s] %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# -------------------------------------------------
# RULE SETS
# -------------------------------------------------

BANK_STATEMENT_KEYWORDS = [
    # generic
    "statement of account",
    "account statement",

    # alternative phrasings
    "details of statement",
    "statement period",
    "statement date",

    # table-driven signals
    "transaction",
    "balance(rs",
    "amount(rs",
    "withdrawal",
    "deposit",

    # Indian banking specific
    "rtgs/neft",
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
        "keywords": [
            "hdfc bank",
            "hdfc bank limited",
            "hdfc",
        ],
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
    "keywords": [
        "kotak mahindra bank",
        "kotak bank",
        "kotak",
    ],
    "ifsc_patterns": [
        r"KKBK\d{7}",
    ],
},

    "AXIS": {
    "keywords": [
        "axis bank",
        "axis",
    ],
    "ifsc_patterns": [
        r"UTIB\d{7}",
    ],
},

}



# -------------------------------------------------
# DOCUMENT TYPE CLASSIFICATION
# -------------------------------------------------

def classify_document_type(text: str) -> Dict:
    text_lower = text.lower()

    bank_score = sum(k in text_lower for k in BANK_STATEMENT_KEYWORDS)
    invoice_score = sum(k in text_lower for k in INVOICE_KEYWORDS)

    logger.info(f"Document type signals → bank:{bank_score}, invoice:{invoice_score}")

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

# -------------------------------------------------
# BANK DETECTION
# -------------------------------------------------

def detect_bank(text: str) -> Dict:
    scores = {}
    text_lower = text.lower()

    for bank, rules in BANK_RULES.items():
        score = 0
        signals = []

        for kw in rules["keywords"]:
            if kw in text_lower:
                score += 2
                signals.append(f"keyword:{kw}")

        for pattern in rules["ifsc_patterns"]:
            if re.search(pattern, text):
                score += 3
                signals.append("ifsc_match")

        if score > 0:
            scores[bank] = {"score": score, "signals": signals}

    if not scores:
        logger.warning("No bank matched")
        return {
            "bank_name": "unknown",
            "confidence": 0.0,
            "signals": [],
        }

    best_bank = max(scores, key=lambda b: scores[b]["score"])
    best_score = scores[best_bank]["score"]
    confidence = min(0.5 + best_score * 0.1, 0.95)

    logger.info(f"Bank detected → {best_bank} (score={best_score})")

    return {
        "bank_name": best_bank,
        "confidence": confidence,
        "signals": scores[best_bank]["signals"],
    }

# -------------------------------------------------
# MAIN CLASSIFIER (ORCHESTRATOR)
# -------------------------------------------------

def classify_pdf(text: str) -> Dict:
    logger.info("Starting PDF classification")

    result = classify_document_type(text)

    if result["doc_type"] != "bank_statement":
        logger.info("Not a bank statement → stopping pipeline")
        result["bank_name"] = None
        return result

    bank_result = detect_bank(text)
    result.update(bank_result)

    return result
