# pdf_parser/parsers/icici/parser_table.py

import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict


DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}")
AMOUNT_RE = re.compile(r"-?[\d,]+\.\d{2}")


def _to_decimal(val: str | None) -> Decimal | None:
    if not val:
        return None
    return Decimal(val.replace(",", ""))


def _to_date(val: str) -> str:
    return datetime.strptime(val, "%d-%m-%Y").date().isoformat()


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

            buffer = ""

            for line in lines:
                # start of transaction row
                if DATE_RE.match(line):
                    buffer = line
                else:
                    buffer += " " + line

                parts = buffer.split()
                if not parts or not DATE_RE.match(parts[0]):
                    continue

                amounts = AMOUNT_RE.findall(buffer)
                if len(amounts) < 2:
                    continue

                date = _to_date(parts[0])
                balance = _to_decimal(amounts[-1])
                withdrawal = _to_decimal(amounts[-2]) if "0.00" not in amounts[-2] else None
                deposit = None

                # ICICI: withdrawals & deposits are explicit
                if " 0.00 " in buffer:
                    nums = [a for a in amounts[:-1] if a != "0.00"]
                    if nums:
                        deposit = _to_decimal(nums[-1])
                        withdrawal = None

                if withdrawal:
                    amount = withdrawal
                    tx_type = "debit"
                elif deposit:
                    amount = deposit
                    tx_type = "credit"
                else:
                    buffer = ""
                    continue

                desc = buffer[len(parts[0]):].strip()

                transactions.append(
                    {
                        "entity_name": None,
                        "transaction_date": date,
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

                buffer = ""

    return transactions
