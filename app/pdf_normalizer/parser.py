"""
Docstring :
> source venv/bin/activate
> source .env

> python app/pdf_normalizer/parser.py files/15547619-XXXXXXX-400008_unlocked.pdf
> python app/pdf_normalizer/parser.py files/hdfc.pdf
"""
from app.pdf_normalizer.banks import UnionBankParser, HdfcBankParser
from app.pdf_normalizer.utils import get_bank_identifier, extract_table_rows, debug_tables
from app.pdf_normalizer.layout_detector import BankDetector

PARSERS = [
    UnionBankParser,
]


def parse_statement(pdf_path: str):
    text = get_bank_identifier(pdf_path)

    detector = BankDetector(PARSERS)
    parser_cls = detector.detect(text)

    parser = parser_cls()

    rows = debug_tables(pdf_path)
    rows = extract_table_rows(pdf_path)
    extract_dict = parser.parse_rows(rows)
    return extract_dict

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract text")
    parser.add_argument("input", help="Input PDF file path")

    args = parser.parse_args()

    result = parse_statement(pdf_path=args.input)
    breakpoint()
    print(result)
