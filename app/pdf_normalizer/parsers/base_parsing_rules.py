from abc import ABC, abstractmethod
from typing import Dict, List
import re
from dateutil.parser import parse as parse_date

class ParsingRule(ABC):
    @abstractmethod
    def match(self, row: List[str]) -> bool:
        ...



class DateAmountRule(ParsingRule):

    @staticmethod
    def is_date(text: str) -> bool:
        """Check if text is a valid date using dateutil."""
        if not text or not text.strip():
            return False

        text = text.strip()

        # Must contain at least one separator or month name
        if not any(c in text for c in "/-") and not any(m in text.lower() for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
            return False

        try:
            parse_date(text)
            return True
        except (ValueError, TypeError):
            return False

    def match(self, row: list[str]) -> tuple[bool, int | None]:
        """Check if row[0] or row[1] contains a date (min 6 chars)."""
        for i in range(min(2, len(row))):
            if row[i] and len(row[i].strip()) >= 6 and self.is_date(row[i]):
                return True, i
        return False, None


