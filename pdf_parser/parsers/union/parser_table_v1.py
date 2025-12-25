import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict


ROW_RE = re.compile(
    r"""
    (?P<date>\d{2}/\d{2}/\d{4})\s+
    (?P<txn_id>\S+)\s+
    (?P<remarks>.+?)\s+
    (?P<amount>[\d,]+\.\d{2})\s+
    \((?P<type>Dr|Cr)\)\s+
    (?P<balance>[\d,]+\.\d{2})
    """,
    re.VERBOSE,
)


def _to_decimal(v: str) -> Decimal:
    return Decimal(v.replace(",", ""))


def _to_date(v: str) -> str:
    return datetime.strptime(v, "%d/%m/%Y").date().isoformat()


def parse_union_table_v1(
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

            for line in lines:
                m = ROW_RE.search(line)
                if not m:
                    continue

                tx_type = "debit" if m.group("type") == "Dr" else "credit"
                amount = _to_decimal(m.group("amount"))
                if tx_type == "debit":
                    amount = abs(amount)

                transactions.append(
                    {
                        "entity_name": None,
                        "transaction_date": _to_date(m.group("date")),
                        "person_id": person_id,
                        "type_id": None,
                        "category_id": None,
                        "tag_id": None,
                        "amount": amount,
                        "balance": _to_decimal(m.group("balance")),
                        "currency": "INR",
                        "payment_method_id": None,
                        "goal_id": None,
                        "description": m.group("remarks"),
                        "remarks": None,
                        "transaction_type": tx_type,
                        "source_bank": "UNION",
                        "source_layout": "UNION_TABLE_V1",
                        "statement_id": statement_id,
                    }
                )

    return transactions
