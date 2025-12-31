"""
Docstring :
> source venv/bin/activate
> source .env

> python app/pdf_normalizer/parser.py files/union.pdf
> python app/pdf_normalizer/parser.py files/15547619-XXXXXXX-400008_unlocked.pdf
> python app/pdf_normalizer/parser.py files/hdfc.pdf
"""
from app.pdf_normalizer.banks import UnionBankParser, HdfcBankParser
from app.pdf_normalizer.utils import get_bank_identifier, extract_table_rows, debug_tables
from app.pdf_normalizer.layout_detector import BankDetector
from app.common.enums import BankName


BANK_PARSER_MAP = {
    BankName.UNION : UnionBankParser
}

def parse_statement(pdf_path: str, bank_name: BankName = None):
    """
    Docstring for parse_statement

    Returns:
        - {
            "account_details: {
                ''

            },
            'transcation_details' : [

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
    transcation_rows = parser.parse_rows(rows)
    details = {
        'account_details' : account_details,
        'transcations' : transcation_rows
    }
    return details

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract text")
    parser.add_argument("input", help="Input PDF file path")

    args = parser.parse_args()

    result = parse_statement(pdf_path=args.input, bank_name= BankName.UNION)
    print(len(result))
    # print(result)

