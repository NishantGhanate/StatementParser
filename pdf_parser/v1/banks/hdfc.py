"""
HDFC Phase-2 parser (TEXT route).

Documented exception:
- pdfplumber tables are unreliable for this statement
- Withdrawal / Deposit columns are not preserved
- transaction_type is derived via closing-balance delta

Behavior matches Phase-1 HDFC outcome.
"""

import re
import pdfplumber
from decimal import Decimal
from typing import List, Dict
from pdf_parser.v1.core.transaction_builder import build_transaction

DATE_RE = re.compile(r"\d{2}/\d{2}/\d{2}")
AMOUNT_RE = re.compile(r"-?\d+(?:,\d+)*(?:\.\d{1,2})?")


def parse_hdfc_v2(pdf_path: str) -> List[Dict]:
    transactions: List[Dict] = []
    prev_balance: Decimal | None = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                if not DATE_RE.match(line):
                    continue

                nums = AMOUNT_RE.findall(line)
                if len(nums) < 2:
                    continue

                amount = Decimal(nums[-2].replace(",", ""))
                balance = Decimal(nums[-1].replace(",", ""))

                if prev_balance is None:
                    txn_type = "debit"
                else:
                    txn_type = "credit" if balance > prev_balance else "debit"

                prev_balance = balance

                date_raw = line[:8]
                desc = re.sub(r"\d{2}/\d{2}/\d{2}.*$", "", line[8:]).strip()
                desc = re.sub(r"\b\d{10,}\b", "", desc)
                desc = re.sub(r"\s{2,}", " ", desc).strip("- ").strip()

                transactions.append(
                    build_transaction(
                        date_raw=date_raw,
                        description=desc,
                        amount_raw=str(abs(amount)),
                        transaction_type=txn_type,
                        entity_name=None,
                    )
                )

    return transactions
