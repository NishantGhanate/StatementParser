from typing import List, Dict
from decimal import Decimal
from dateutil import parser as date_parser
import pdfplumber

from pdf_parser.v1.core.transaction_builder import build_transaction


def parse_union_table(pdf_path: str) -> List[Dict]:
    transactions: List[Dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 6:
                        continue

                    try:
                        txn_date = row[1]
                        date_parser.parse(txn_date, dayfirst=True)
                    except Exception:
                        continue

                    description = row[2] or ""

                    withdrawal = row[4].replace(",", "").strip() if row[4] else ""
                    deposit = row[5].replace(",", "").strip() if row[5] else ""

                    if withdrawal:
                        amount = withdrawal
                        txn_type = "debit"
                    elif deposit:
                        amount = deposit
                        txn_type = "credit"
                    else:
                        continue

                    transactions.append(
                        build_transaction(
                            txn_date,
                            description,
                            amount,
                            txn_type,
                            entity_name=None,
                        )
                    )

    return transactions
