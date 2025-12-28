
from .banks import UnionBankParser
from .utils import extract_text, extract_tables_as_plain_text
from .layout_detector import BankDetector

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
    result = parse_statement(pdf_path='')
