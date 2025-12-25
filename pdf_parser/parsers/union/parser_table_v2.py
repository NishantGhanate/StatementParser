import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict


ROW_START_RE = re.compile(r"^\d+\s+\d{2}-\d{2}-\d{4}")
BALANCE_RE = re.compile(r"([\d,]+\.\d{2})\s+Cr")
AMOUNT_RE = re.compile(r"[\d,]+\.\d{2}")


def _to_decimal(v: str) -> Decimal:
    return Decimal(v.replace(",", ""))


def _to_date(v: str) -> str:
    return datetime.strptime(v, "%d-%m-%Y").date().isoformat()


def parse_union_table_v2(
    pdf_path: str,
    *,
    person_id: int,
    statement_id: str,
) -> List[Dict]:

    transactions: List[Dict] = []
    buffer = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = [
                l.strip()
                for l in (page.extract_text() or "").splitlines()
                if l.strip()
            ]

            for line in lines:

                # HARD STOP before summary contamination
                if line.lower().startswith("summary"):
                    if buffer:
                        buffer = ""
                    return transactions

                # Start of new transaction
                if ROW_START_RE.match(line):
                    if buffer:
                        buffer = ""
                    buffer = line
                    continue

                # Append continuation lines
                if buffer:
                    buffer += " " + line

                # Process row when BALANCE appears (NOT summary)
                if buffer and BALANCE_RE.search(buffer):
                    parts = buffer.split()
                    date = _to_date(parts[1])

                    nums = AMOUNT_RE.findall(buffer)
                    if len(nums) < 2:
                        buffer = ""
                        continue

                    balance = _to_decimal(nums[-1])
                    amount = _to_decimal(nums[-2])

                    # UNION V2 rule:
                    # If balance increased → credit
                    # If balance decreased → debit
                    if transactions:
                        prev_balance = transactions[-1]["balance"]
                        tx_type = "credit" if balance > prev_balance else "debit"
                    else:
                        # first row: infer from text
                        tx_type = "credit" if "/CR/" in buffer else "debit"

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
                            "description": buffer,
                            "remarks": None,
                            "transaction_type": tx_type,
                            "source_bank": "UNION",
                            "source_layout": "UNION_TABLE_V2",
                            "statement_id": statement_id,
                        }
                    )

                    buffer = ""

    return transactions
