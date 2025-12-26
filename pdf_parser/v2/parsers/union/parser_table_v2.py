import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional


ROW_START_RE = re.compile(r"^\d+\s+\d{2}-\d{2}-\d{4}")
BALANCE_RE = re.compile(r"([\d,]+\.\d{2})\s+Cr", re.IGNORECASE)
AMOUNT_RE = re.compile(r"[\d,]+\.\d{2}")


def _to_decimal(v: str) -> Optional[Decimal]:
    try:
        return Decimal(v.replace(",", ""))
    except Exception:
        return None


def _to_date(v: str) -> Optional[str]:
    try:
        return datetime.strptime(v, "%d-%m-%Y").date().isoformat()
    except Exception:
        return None


def parse_union_table_v2(
    pdf_path: str,
    *,
    person_id: int,
    statement_id: str,
) -> List[Dict]:

    transactions: List[Dict] = []
    buffer: Optional[str] = None
    prev_balance: Optional[Decimal] = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = [
                l.strip()
                for l in (page.extract_text() or "").splitlines()
                if l.strip()
            ]

            for line in lines:

                if line.lower().startswith("summary"):
                    buffer = None
                    return transactions

                if ROW_START_RE.match(line):
                    buffer = line
                    continue

                if buffer:
                    buffer += " " + line

                if buffer and BALANCE_RE.search(buffer):
                    parts = buffer.split()
                    if len(parts) < 2:
                        buffer = None
                        continue

                    tx_date = _to_date(parts[1])
                    nums = AMOUNT_RE.findall(buffer)

                    if tx_date is None or len(nums) < 2:
                        buffer = None
                        continue

                    balance = _to_decimal(nums[-1])
                    amount = _to_decimal(nums[-2])

                    if balance is None or amount is None:
                        buffer = None
                        continue

                    if prev_balance is not None:
                        tx_type = "credit" if balance > prev_balance else "debit"
                    else:
                        tx_type = "credit" if "/CR/" in buffer.upper() else "debit"

                    transactions.append(
                        {
                            "entity_name": None,
                            "transaction_date": tx_date,
                            "person_id": person_id,
                            "type_id": None,
                            "category_id": None,
                            "tag_id": None,
                            "amount": amount,
                            "balance": balance,
                            "currency": "INR",
                            "payment_method_id": None,
                            "goal_id": None,
                            "description": buffer,
                            "remarks": None,
                            "transaction_type": tx_type,
                            "source_bank": "UNION",
                            "source_layout": "UNION_TABLE_V2",
                            "statement_id": statement_id,
                        }
                    )

                    prev_balance = balance
                    buffer = None

    return transactions
