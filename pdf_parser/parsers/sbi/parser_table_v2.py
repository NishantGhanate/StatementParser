import pdfplumber
import logging
from decimal import Decimal
from datetime import datetime
from typing import List, Dict
import re

logger = logging.getLogger("SBI_TABLE_V2_PARSER")
logger.setLevel(logging.INFO)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def _normalize_date(date_str: str) -> str:
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date().isoformat()
        except Exception:
            continue
    raise ValueError("Invalid date")


def _to_decimal(val) -> Decimal | None:
    if val is None:
        return None
    s = str(val).replace(",", "").replace("₹", "").strip()
    if not re.search(r"\d", s):
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def _clean(cell) -> str:
    return "" if cell is None else str(cell).strip()


def _extract_reference(desc: str) -> str | None:
    m = re.search(r"(UPI|IMPS|NEFT|RTGS|REF)[-/ ]?[\w\d]+", desc, re.IGNORECASE)
    return m.group(0) if m else None


def _extract_opening_balance(text: str) -> Decimal | None:
    m = re.search(
        r"Your Opening Balance on .*?:\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    return Decimal(m.group(1).replace(",", ""))


# -------------------------------------------------
# MAIN PARSER — SBI TABLE V2 (FINAL)
# -------------------------------------------------
def parse_sbi_table_v2(
    pdf_path: str,
    *,
    person_id: int,
    statement_id: str,
    raw_text: str | None = None,
) -> List[Dict]:

    ledger_rows: List[Dict] = []

    # -------------------------------------------------
    # STEP 1: Extract ledger rows (multi-page safe)
    # -------------------------------------------------
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables(
                {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_tolerance": 5,
                }
            )

            if not tables:
                continue

            for table in tables:
                if not table or len(table) < 2:
                    continue

                rows = [[_clean(c) for c in r] for r in table]

                header = " ".join(rows[0]).lower()
                if not (
                    "date" in header
                    and "balance" in header
                    and ("credit" in header or "debit" in header)
                ):
                    continue

                for row in rows[1:]:
                    if len(row) < 5:
                        continue

                    date_raw = row[0]
                    desc = row[1]
                    balance_raw = row[-1]

                    # 🚫 HARD SKIP bogus header/null rows
                    if not date_raw or desc.lower() in ("null", ""):
                        continue

                    try:
                        tx_date = _normalize_date(date_raw)
                        balance = _to_decimal(balance_raw)
                    except Exception:
                        continue

                    if balance is None:
                        continue

                    ledger_rows.append(
                        {
                            "date": tx_date,
                            "description": desc.strip(),
                            "balance": balance,
                        }
                    )

    # -------------------------------------------------
    # STEP 2: Balance-delta computation (CORRECT)
    # -------------------------------------------------
    transactions: List[Dict] = []

    opening_balance = _extract_opening_balance(raw_text) if raw_text else None
    prev_balance: Decimal | None = opening_balance

    for row in ledger_rows:
        if prev_balance is None:
            prev_balance = row["balance"]
            continue

        delta = row["balance"] - prev_balance
        if delta == 0:
            prev_balance = row["balance"]
            continue

        transaction_type = "credit" if delta > 0 else "debit"

        transactions.append(
            {
                "entity_name": None,
                "transaction_date": row["date"],
                "person_id": person_id,
                "type_id": None,
                "category_id": None,
                "tag_id": None,
                "amount": abs(delta),
                "currency": "INR",
                "payment_method_id": None,
                "goal_id": None,
                "description": row["description"],
                "remarks": _extract_reference(row["description"]),
                "transaction_type": transaction_type,
                "source_bank": "SBI",
                "source_layout": "SBI_TABLE_V2",
                "statement_id": statement_id,
            }
        )

        prev_balance = row["balance"]

    logger.info(f"SBI_TABLE_V2 parsed {len(transactions)} transactions")
    return transactions
