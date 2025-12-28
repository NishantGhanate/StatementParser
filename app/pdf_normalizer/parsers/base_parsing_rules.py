from abc import ABC, abstractmethod
from typing import Dict, List
import re

class ParsingRule(ABC):
    @abstractmethod
    def match(self, row: List[str]) -> bool:
        ...

    @abstractmethod
    def extract(self, row: List[str]) -> Dict:
        ...


class DateAmountRule(ParsingRule):
    def match(self, row):
        return bool(re.match(r"\d{2}/\d{2}/\d{4}", row[0]))

    def extract(self, row):
        return {
            "date": row[0],
            "description": row[1],
            "debit": row[2],
            "credit": row[3],
            "balance": row[4],
        }
