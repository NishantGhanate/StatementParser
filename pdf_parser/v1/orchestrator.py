"""
v1 orchestrator.

SBI → table + rules
HDFC → text-based exception
"""
from typing import List, Dict

from pdf_parser.v1.core.table_extractor import extract_tables
from pdf_parser.v1.rules.sbi_rules import SbiTxnRowRule
from pdf_parser.v1.core.transaction_builder import build_transaction
from pdf_parser.v1.banks.hdfc import parse_hdfc_v2


def parse_statement(pdf_path: str, bank: str) -> List[Dict]:
    bank = bank.upper()

    # HDFC exception path
    if bank == "HDFC":
        return parse_hdfc_v2(pdf_path)

    # SBI default path
    if bank == "SBI":
        rows = extract_tables(pdf_path)
        rule = SbiTxnRowRule()
        transactions: List[Dict] = []

        for row in rows:
            if not rule.match(row):
                continue
            data = rule.extract(row)
            transactions.append(build_transaction(**data))

        return transactions

    raise ValueError(f"Unsupported bank: {bank}")
