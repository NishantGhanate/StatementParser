"""
PDF statement parser entry point
"""

from app.pdf_normalizer.banks import UnionBankParser
from app.pdf_normalizer.layout_detector import BankDetector
from app.pdf_normalizer.text_extractor import extract_text
from app.pdf_normalizer.utils import extract_table_rows
from app.common.enums import BankName

PARSERS = [
    UnionBankParser,
]

BANK_PARSER_MAP = {
    BankName.UNION: UnionBankParser,
}


def parse_statement(pdf_path: str, bank_name: BankName = None):
    """
    Parses a bank statement PDF and returns transaction rows.
    Also attaches full PDF text to each transaction for metadata parsing.
    """


    text = extract_text(pdf_path)

   
    if not bank_name:
        detector = BankDetector(PARSERS)
        parser_cls = detector.detect(text)
    else:
        parser_cls = BANK_PARSER_MAP[bank_name]

    parser = parser_cls()

   
    rows = extract_table_rows(pdf_path)
    transactions = parser.parse_rows(rows)


    for tx in transactions:
        tx["_full_text"] = text

    return transactions


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="PDF path")
    args = parser.parse_args()

    result = parse_statement(
        pdf_path=args.input,
        bank_name=BankName.UNION,
    )

    print(f"Parsed {len(result)} transactions")
