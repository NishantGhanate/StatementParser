import re
from app.pdf_normalizer.parsers.base_parser import BankStatementParser
from app.pdf_normalizer.parsers.base_parsing_rules import DateAmountRule

class HdfcBankParser(BankStatementParser):
    rules = [DateAmountRule()]
    bank_name = "HDFC"


    def detect(self, text: str) -> bool:
        is_union = "hdfc" in text.lower()
        return is_union


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
