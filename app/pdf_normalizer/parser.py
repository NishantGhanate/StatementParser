"""
Docstring :
> source venv/bin/activate
> source .env

> python app/pdf_normalizer/parser.py files/union.pdf
> python app/pdf_normalizer/parser.py files/15547619-XXXXXXX-400008_unlocked.pdf
> python app/pdf_normalizer/parser.py files/hdfc.pdf
"""
from app.common.enums import BankName
from app.pdf_normalizer.banks import HdfcBankParser, UnionBankParser, SBIBankParser
from app.pdf_normalizer.layout_detector import BankDetector
from app.pdf_normalizer.utils import (debug_tables, extract_table_rows,
                                      get_bank_identifier)

BANK_PARSER_MAP = {
    BankName.UNION : UnionBankParser,
    BankName.SBI : SBIBankParser,
}

def parse_statement(pdf_path: str, bank_name: BankName = None):
    """
    Docstring for parse_statement

    - Returns:
        - {
            "account_details: {
                ''

            },
            'transactions' : [

            ]
        }
    """
    text = get_bank_identifier(pdf_path)

    if not bank_name:
        detector = BankDetector(list(BANK_PARSER_MAP.values()))
        parser_cls = detector.detect(text)
    else:
        parser_cls = BANK_PARSER_MAP[bank_name]

    parser = parser_cls()

    # rows = debug_tables(pdf_path)
    rows = extract_table_rows(pdf_path)
    account_details = parser.parse_account_details(text= text)
    transactions = parser.parse_rows(rows)
    details = {
        'account_details' : account_details,
        'transactions' : transactions
    }
    return details

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract text")
    parser.add_argument("input", help="Input PDF file path")

    args = parser.parse_args()

    result = parse_statement(pdf_path=args.input)
    # print(len(result))
    print(result)

