import logging
from typing import List, Type
from app.pdf_normalizer.parsers.base_parser import BankStatementParser

logger = logging.getLogger("app")

class BankDetector:
    def __init__(self, parsers: List[Type[BankStatementParser]]):
        self.parsers = parsers

    def detect(self, text: str) -> Type[BankStatementParser]:
        for parser_cls in self.parsers:
            parser = parser_cls()
            if parser.detect(text):
                logger.info(f"Detected: {text}")
                return parser_cls
        raise ValueError("Unsupported bank statement")
