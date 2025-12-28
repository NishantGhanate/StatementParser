from typing import List, Type
from .parsers.base_parser import BankStatementParser


class BankDetector:
    def __init__(self, parsers: List[Type[BankStatementParser]]):
        self.parsers = parsers

    def detect(self, text: str) -> Type[BankStatementParser]:
        for parser_cls in self.parsers:
            parser = parser_cls()
            if parser.detect(text):
                return parser_cls
        raise ValueError("Unsupported bank statement")
