from abc import ABC, abstractmethod
from typing import List, Dict

Transaction = Dict[str, str]

class BankStatementParser(ABC):

    bank_name: str


    @abstractmethod
    def detect(self, text: str) -> bool:
        """Return True if this parser matches the statement"""

    @abstractmethod
    def extract_tables(self, pdf_path: str) -> List[List[str]]:
        """Return table rows (list of columns)"""

    @abstractmethod
    def parse_rows(self, rows: List[List[str]]) -> List[Transaction]:
        """Convert rows → normalized transactions"""
