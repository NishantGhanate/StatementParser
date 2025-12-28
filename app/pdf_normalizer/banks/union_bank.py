import re
import pdfplumber
from typing import List
from ..parsers.base_parser import BaseBankParser
from ..parsers.base_parsing_rules import DateAmountRule

class UnionBankParser(BaseBankParser):
    rules = [DateAmountRule()]
    bank_name = "UNION"

    def detect(self, text: str) -> bool:
        return bool(re.search(r"Union Bank of India", text, re.I))

    def parse_rows(self, rows):
        """
        Docstring for parse_rows

        :param rows: Description
        """
        txns = []
        for row in rows:
            for rule in self.rules:
                if rule.match(row):
                    txns.append(rule.extract(row))
        return txns
