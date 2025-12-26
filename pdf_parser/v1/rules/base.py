"""
Strict rule contract.
"""
from abc import ABC, abstractmethod
from typing import Dict, List


class Rule(ABC):
    """
    Base rule for row parsing.
    """

    @abstractmethod
    def match(self, row: List[str]) -> bool:
        """
        Determine if rule applies to row.
        """
        ...

    @abstractmethod
    def extract(self, row: List[str]) -> Dict:
        """
        Extract normalized fields from row.
        """
        ...
