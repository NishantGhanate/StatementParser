import re
import logging
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional


logger = logging.getLogger("SBI_TABLE_V1_PARSER")
logger.setLevel(logging.INFO)


DATE_RE = re.compile(r"^(\d{2}[-/]\d{2}[-/]\d{2,4})")
AMOUNT_RE = re.compile(r"\b\d{1,3}(?:,\d{3})*\.\d{2}\b")
DR_RE = re.compile(r"\bDR\b|/DR\b", re.IGNORECASE)
CR_RE = re.compile(r"\bCR\b|/CR\b", re.IGNORECASE)

AMOUNT_BALANCE_RE = re.compile(
    r"\b\d{1,3}(?:,\d{3})*\.\d{2}\s+\d{1,3}(?:,\d{3})*\.\d{2}\b"
)

TABLE_END_KEYWORDS = [
    "your opening balance",
    "your closing balance",
    "contents of this statement",
    "all dates are in",
]

NOISE_KEYWORDS = [
    "balance summary",
    "transaction details",
    "statement of account",
    "customer care",
    "welcome",
    "registered office",
    "branch address",
    "page ",
]


def parse_sbi_table_v1(
    text: str,
    *,
    person_id: int,
    statement_id: str,
) -> List[Dict]:

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    start_index: Optional[int] = None
    for i, line in enumerate(lines):
        l = line.lower()
        if all(k in l for k in ("date", "debit", "credit", "balance")):
            start_index = i + 1
            break

    if start_index is None:
        logger.warning("SBI_TABLE_V1 header not found")
        return []

    transactions = []
    current = None

    for line in lines[start_index:]:
        lline = line.lower()

        if any(k in lline for k in TABLE_END_KEYWORDS):
            break

        if any(k in lline for k in NOISE_KEYWORDS):
            continue

        date_match = DATE_RE.match(line)
        amounts = AMOUNT_RE.findall(line)
        has_amount_balance = bool(AMOUNT_BALANCE_RE.search(line))

        if date_match or has_amount_balance:
            if current:
                transactions.extend(_finalize_buffer(current))

            if not date_match:
                logger.warning("Row without date encountered, skipping")
                current = None
                continue

            current = {
                "date_raw": date_match.group(1),
                "description": line[len(date_match.group(1)):].strip(),
                "amounts": amounts.copy(),
                "has_dr": bool(DR_RE.search(line)),
                "has_cr": bool(CR_RE.search(line)),
                "person_id": person_id,
                "statement_id": statement_id,
            }

        elif current:
            current["description"] += " " + line
            current["amounts"].extend(amounts)
            current["has_dr"] |= bool(DR_RE.search(line))
            current["has_cr"] |= bool(CR_RE.search(line))

    if current:
        transactions.extend(_finalize_buffer(current))

    return transactions


def _finalize_buffer(buf: Dict) -> List[Dict]:
    results = []

    try:
        tx_date = _normalize_date(buf["date_raw"])
    except Exception:
        logger.warning(f"Invalid date skipped: {buf['date_raw']}")
        return results

    amounts = buf["amounts"]

    if len(amounts) < 2:
        logger.warning("Insufficient amount data, skipping row")
        return results

    pairs = []
    for i in range(0, len(amounts) - 1, 2):
        pairs.append((amounts[i], amounts[i + 1]))

    has_dr = buf["has_dr"]
    has_cr = buf["has_cr"]

    if has_dr and has_cr:
        logger.warning("Both DR and CR found, skipping row")
        return results

    if not has_dr and not has_cr:
        logger.warning("No DR/CR indicator, skipping row")
        return results

    transaction_type = "debit" if has_dr else "credit"
    desc = buf["description"].strip()

    for amt, balance in pairs:
        results.append(
            {
                "entity_name": None,
                "transaction_date": tx_date,
                "person_id": buf["person_id"],
                "type_id": None,
                "category_id": None,
                "tag_id": None,
                "amount": Decimal(amt.replace(",", "")),
                "balance": Decimal(balance.replace(",", "")),
                "currency": "INR",
                "payment_method_id": None,
                "goal_id": None,
                "description": desc,
                "remarks": _extract_reference(desc),
                "transaction_type": transaction_type,
                "source_bank": "SBI",
                "source_layout": "SBI_TABLE_V1",
                "statement_id": buf["statement_id"],
            }
        )

    return results


def _extract_reference(desc: str) -> Optional[str]:
    m = re.search(r"(UPI|IMPS|NEFT|RTGS)[-/ ]?[\w\d]+", desc, re.IGNORECASE)
    return m.group(0) if m else None


def _normalize_date(date_str: str) -> str:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Invalid date")
