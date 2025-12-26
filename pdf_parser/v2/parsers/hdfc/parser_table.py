import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional


ROW_RE = re.compile(
    r"""
    (?P<date>\d{2}/\d{2}/\d{2})\s+
    (?P<desc>.+?)\s+
    (?P<ref>\d{6,})\s+
    (?P<valdt>\d{2}/\d{2}/\d{2})\s+
    (?P<debit>[\d,]+\.\d{2})?\s*
    (?P<credit>[\d,]+\.\d{2})?\s+
    (?P<balance>[\d,]+\.\d{2})
    """,
    re.VERBOSE,
)


def _to_decimal(val: Optional[str]) -> Optional[Decimal]:
    if not val:
        return None
    try:
        return Decimal(val.replace(",", ""))
    except Exception:
        return None


def _to_date(val: str) -> Optional[str]:
    try:
        return datetime.strptime(val, "%d/%m/%y").date().isoformat()
    except Exception:
        return None


def parse_hdfc_table(
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
                if re.match(r"\d{2}/\d{2}/\d{2}", line):
                    buffer = line
                elif buffer:
                    buffer += " " + line
                else:
                    continue

                m = ROW_RE.search(buffer)
                if not m:
                    continue

                tx_date = _to_date(m.group("date"))
                balance = _to_decimal(m.group("balance"))
                debit = _to_decimal(m.group("debit"))
                credit = _to_decimal(m.group("credit"))

                if tx_date is None or balance is None:
                    buffer = None
                    continue

                if debit is not None:
                    amount = debit
                    tx_type = "debit"
                elif credit is not None:
                    amount = credit
                    tx_type = "credit"
                else:
                    buffer = None
                    continue

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
                        "description": m.group("desc").strip(),
                        "remarks": m.group("ref"),
                        "transaction_type": tx_type,
                        "source_bank": "HDFC",
                        "source_layout": "HDFC_TEXT",
                        "statement_id": statement_id,
                    }
                )

                buffer = None

    return transactions
