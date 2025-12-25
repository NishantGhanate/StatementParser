import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict


# -------------------------------------------------
# REGEX — ONE TRANSACTION ROW
# -------------------------------------------------
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


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def _to_decimal(val: str | None) -> Decimal | None:
    if not val:
        return None
    return Decimal(val.replace(",", ""))


def _to_date(val: str) -> str:
    return datetime.strptime(val, "%d/%m/%y").date().isoformat()


# -------------------------------------------------
# MAIN PARSER — HDFC (TEXT BASED)
# -------------------------------------------------
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

            buffer = ""

            for line in lines:
                # Start of new transaction
                if re.match(r"\d{2}/\d{2}/\d{2}", line):
                    buffer = line
                else:
                    buffer += " " + line

                m = ROW_RE.search(buffer)
                if not m:
                    continue

                tx_date = _to_date(m.group("date"))
                desc = m.group("desc").strip()
                debit = _to_decimal(m.group("debit"))
                credit = _to_decimal(m.group("credit"))
                balance = _to_decimal(m.group("balance"))

                # TEMP direction (will be fixed by balance delta)
                if debit:
                    amount = debit
                    tx_type = "debit"
                elif credit:
                    amount = credit
                    tx_type = "credit"
                else:
                    buffer = ""
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
                        "balance": balance,           # 🔑 IMPORTANT
                        "currency": "INR",
                        "payment_method_id": None,
                        "goal_id": None,
                        "description": desc,
                        "remarks": None,
                        "transaction_type": tx_type,  # will be corrected
                        "source_bank": "HDFC",
                        "source_layout": "HDFC_TEXT",
                        "statement_id": statement_id,
                    }
                )

                buffer = ""

    return transactions
