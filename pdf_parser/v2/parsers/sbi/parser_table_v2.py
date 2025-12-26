import pdfplumber
import logging
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional
import re

logger = logging.getLogger("SBI_TABLE_V2_PARSER")
logger.setLevel(logging.INFO)

DATE_RE = re.compile(r"\b\d{2}[-/]\d{2}[-/]\d{2,4}\b")
AMOUNT_RE = re.compile(r"[\d,]+\.\d{2}")


def _normalize_date(date_str: str) -> Optional[str]:
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date().isoformat()
        except Exception:
            continue
    return None


def _to_decimal(val: str) -> Optional[Decimal]:
    try:
        return Decimal(val.replace(",", ""))
    except Exception:
        return None


def _extract_opening_balance(text: Optional[str]) -> Optional[Decimal]:
    if not text:
        return None
    m = re.search(
        r"Your Opening Balance on .*?:\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    return _to_decimal(m.group(1))


def parse_sbi_table_v2(
    pdf_path: str,
    *,
    person_id: int,
    statement_id: str,
    raw_text: Optional[str] = None,
) -> List[Dict]:

    ledger_rows: List[Dict] = []

    # -------------------------------------------------
    # STEP 1: Extract ledger rows
    # -------------------------------------------------
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            for line in lines:
                dates = DATE_RE.findall(line)
                nums = AMOUNT_RE.findall(line)

                if not dates or len(nums) < 2:
                    continue

                tx_date = _normalize_date(dates[0])
                if not tx_date:
                    continue

                balance = _to_decimal(nums[-1])
                if balance is None:
                    continue

                ledger_rows.append(
                    {
                        "date": tx_date,
                        "raw": line,
                        "numbers": nums,
                        "balance": balance,
                    }
                )

    if not ledger_rows:
        return []

    # -------------------------------------------------
    # STEP 2: Build transactions using balance deltas
    # -------------------------------------------------
    transactions: List[Dict] = []

    opening_balance = _extract_opening_balance(raw_text)
    prev_balance: Optional[Decimal] = opening_balance
    first_row = True

    for row in ledger_rows:
        balances = [_to_decimal(n) for n in row["numbers"] if _to_decimal(n) is not None]

        if len(balances) < 2:
            continue

        for i in range(1, len(balances)):
            curr_balance = balances[i]

            if first_row and prev_balance is not None:
                delta = curr_balance - prev_balance
                first_row = False
            else:
                if prev_balance is None:
                    prev_balance = curr_balance
                    continue
                delta = curr_balance - prev_balance

            if delta == 0:
                prev_balance = curr_balance
                continue

            tx_type = "credit" if delta > 0 else "debit"

            transactions.append(
                {
                    "entity_name": None,
                    "transaction_date": row["date"],
                    "person_id": person_id,
                    "type_id": None,
                    "category_id": None,
                    "tag_id": None,
                    "amount": abs(delta),
                    "balance": curr_balance,
                    "currency": "INR",
                    "payment_method_id": None,
                    "goal_id": None,
                    "description": row["raw"],
                    "remarks": None,
                    "transaction_type": tx_type,
                    "source_bank": "SBI",
                    "source_layout": "SBI_TABLE_V2",
                    "statement_id": statement_id,
                }
            )

            prev_balance = curr_balance

    logger.info(f"SBI_TABLE_V2 parsed {len(transactions)} transactions")
    return transactions
