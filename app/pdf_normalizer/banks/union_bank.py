import re
from app.pdf_normalizer.parsers.base_parser import BankStatementParser
from app.pdf_normalizer.parsers.base_parsing_rules import DateAmountRule
from app.pdf_normalizer.utils import transform_dict
from app.pdf_normalizer.values_extract import (
    parse_amount, extract_payment_method, determine_transaction_type,
    extract_entity_name, parse_date
)


class UnionBankParser(BankStatementParser):
    rules = [DateAmountRule()]
    bank_name = "UNION"


    def detect(self, text: str) -> bool:
        is_union = "ubin" in text.lower()
        return is_union

    def parse_rows(self, rows):
        """
        Docstring for parse_rows

        :param rows: Description
        """
        txns = []
        for row in rows:
            for rule in self.rules:
                is_match, index = rule.match(row)
                if is_match:
                    template = transform_dict()

                    template['transaction_date'] = parse_date(row[index])
                    template['reference_id'] = row[1]
                    template['description'] = row[2]
                    template['entity_name'] = extract_entity_name(row[2])

                    template['amount'] = parse_amount(row[-2])
                    template['type'] = determine_transaction_type(row[-2])
                    template['payment_method'] = extract_payment_method(row[2])
                    txns.append(template)
        return txns
