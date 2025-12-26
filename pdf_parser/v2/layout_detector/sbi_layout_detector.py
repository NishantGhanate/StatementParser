import re
from typing import Dict


DATE_RE = re.compile(r"\b\d{2}[-/]\d{2}[-/]\d{2,4}\b")
AMOUNT_RE = re.compile(r"\b\d{1,3}(?:,\d{3})*\.\d{2}\b")
DRCR_RE = re.compile(r"\bDR\b|\bCR\b|/DR\b|/CR\b", re.IGNORECASE)
AMOUNT_BALANCE_RE = re.compile(
    r"\b\d{1,3}(?:,\d{3})*\.\d{2}\s+\d{1,3}(?:,\d{3})*\.\d{2}\b"
)


def detect_sbi_layout(text: str) -> Dict[str, str]:
    dates = DATE_RE.findall(text)
    amounts = AMOUNT_RE.findall(text)
    drcr = DRCR_RE.findall(text)
    pairs = AMOUNT_BALANCE_RE.findall(text)

    date_count = len(dates)
    amount_count = len(amounts)
    drcr_count = len(drcr)
    pair_count = len(pairs)

    if date_count == 0:
        return {
            "bank": "SBI",
            "layout": "UNKNOWN",
        }

    if (
        (amount_count / max(date_count, 1)) > 1.8
        or pair_count >= date_count
        or (amount_count > 0 and drcr_count < amount_count * 0.4)
    ):
        return {
            "bank": "SBI",
            "layout": "SBI_TABLE_V2",
        }

    return {
        "bank": "SBI",
        "layout": "SBI_TABLE_V1",
    }
