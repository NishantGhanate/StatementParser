from typing import List, Dict

from pdf_parser.v1.core.table_extractor import extract_tables
from pdf_parser.v1.core.transaction_builder import build_transaction
from pdf_parser.v1.rules.icici_rules import IciciTxnRowRule


def parse_icici_table(pdf_path: str) -> List[Dict]:
    rows = extract_tables(pdf_path)
    rule = IciciTxnRowRule()

    transactions: List[Dict] = []

    for row in rows:
        if not rule.match(row):
            continue

        data = rule.extract(row)
        if not data:
            continue

        transactions.append(
            build_transaction(
                data["date_raw"],
                data["description"],
                data["amount_raw"],
                data["transaction_type"],
                entity_name=None,
            )
        )

    return transactions
