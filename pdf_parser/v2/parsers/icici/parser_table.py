import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional


DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}")
AMOUNT_RE = re.compile(r"-?[\d,]+\.\d{2}")


def _to_decimal(val: Optional[str]) -> Optional[Decimal]:
    if not val:
        return None
    try:
        return Decimal(val.replace(",", ""))
    except Exception:
        return None


def _to_date(val: str) -> Optional[str]:
    try:
        return datetime.strptime(val, "%d-%m-%Y").date().isoformat()
    except Exception:
        return None


def parse_icici_table(
    pdf_path: str,
    *,
    person_id: int,
    statement_id: str,
) -> List[Dict]:

    transactions: List[Dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            buffer: Optional[str] = None

            for line in lines:
                if DATE_RE.match(line):
                    buffer = line
                elif buffer:
                    buffer += " " + line
                else:
                    continue

                parts = buffer.split()
                if not parts or not DATE_RE.match(parts[0]):
                    continue

                amounts = AMOUNT_RE.findall(buffer)
                if len(amounts) < 2:
                    continue

                tx_date = _to_date(parts[0])
                balance = _to_decimal(amounts[-1])

                if tx_date is None or balance is None:
                    buffer = None
                    continue

                withdrawal = _to_decimal(amounts[-2]) if amounts[-2] != "0.00" else None
                deposit: Optional[Decimal] = None

                if " 0.00 " in buffer:
                    nums = [a for a in amounts[:-1] if a != "0.00"]
                    if nums:
                        deposit = _to_decimal(nums[-1])
                        withdrawal = None

                if withdrawal is not None:
                    amount = withdrawal
                    tx_type = "debit"
                elif deposit is not None:
                    amount = deposit
                    tx_type = "credit"
                else:
                    buffer = None
                    continue

                desc = buffer[len(parts[0]):].strip()

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
                        "description": desc,
                        "remarks": None,
                        "transaction_type": tx_type,
                        "source_bank": "ICICI",
                        "source_layout": "ICICI_TABLE",
                        "statement_id": statement_id,
                    }
                )

                buffer = None

    return transactions
