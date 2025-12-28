"""
Docstring :
> source venv/bin/activate
> source .env
> python app/pdf_normalizer/parser.py files/15547619-XXXXXXX-400008_unlocked.pdf

"""
from app.pdf_normalizer.banks import UnionBankParser
from app.pdf_normalizer.utils import extract_text, extract_tables_as_plain_text
from app.pdf_normalizer.layout_detector import BankDetector

PARSERS = [
    UnionBankParser
]


def parse_statement(pdf_path: str):
    text = extract_text(pdf_path)

    detector = BankDetector(PARSERS)
    parser_cls = detector.detect(text)

    parser = parser_cls()
    rows = extract_tables_as_plain_text(pdf_path)
    return parser.parse_rows(rows)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract text")
    parser.add_argument("input", help="Input PDF file path")

    args = parser.parse_args()

    result = parse_statement(pdf_path=args.input)
    print(result)
