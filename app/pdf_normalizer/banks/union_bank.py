import re

from app.pdf_normalizer.parsers.base_parser import BankStatementParser
from app.pdf_normalizer.parsers.base_parsing_rules import DateAmountRule
from app.pdf_normalizer.utils import (account_details_dict,
                                      ss_transactions_template)
from app.pdf_normalizer.values_extract import (determine_transaction_type,
                                               extract_entity_name,
                                               extract_payment_method,
                                               parse_amount, parse_date)


class UnionBankParser(BankStatementParser):
    rules = [DateAmountRule()]
    bank_name = "UNION"


    def detect(self, text: str) -> bool:
        is_union = "ubin" in text.lower()
        return is_union

    def parse_account_details(self, text):
        """
        Given pdf text extract account details like
        - account_number
        - ifsc_code
        - account_type

        :param text: Description
        """

        result = account_details_dict()

        text_upper = text.upper()

        # Account Number patterns
        acc_patterns = [
            r'ACCOUNT\s*(?:NUMBER|NO\.?|#)\s*[:\-]?\s*(\d{9,18})',
            r'A/C\s*(?:NO\.?|NUMBER)\s*[:\-]?\s*(\d{9,18})',
            r'ACCT\s*(?:NO\.?|NUMBER)\s*[:\-]?\s*(\d{9,18})',
        ]

        for pattern in acc_patterns:
            match = re.search(pattern, text_upper)
            if match:
                result['number'] = match.group(1)
                break

        # IFSC Code pattern (4 letters + 0 + 6 alphanumeric)
        ifsc_match = re.search(r'IFSC\s*(?:CODE)?\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})', text_upper)
        if ifsc_match:
            result['ifsc_code'] = ifsc_match.group(1)
        else:
            # Try finding IFSC pattern without label
            ifsc_match = re.search(r'\b([A-Z]{4}0[A-Z0-9]{6})\b', text_upper)
            if ifsc_match:
                result['ifsc_code'] = ifsc_match.group(1)

        # Account Type patterns
        type_patterns = [
            r'ACCOUNT\s*TYPE\s*[:\-]?\s*(SAVINGS?|CURRENT|SALARY|NRE|NRO|FIXED DEPOSIT|FD|RD|RECURRING)',
            r'A/C\s*TYPE\s*[:\-]?\s*(SAVINGS?|CURRENT|SALARY|NRE|NRO)',
            r'(SAVINGS?|CURRENT|SALARY)\s*ACCOUNT',
        ]

        for pattern in type_patterns:
            match = re.search(pattern, text_upper)
            if match:
                acc_type = match.group(1).strip()
                # Normalize
                if acc_type.startswith('SAVING'):
                    result['type'] = 'SAVINGS'
                else:
                    result['type'] = acc_type
                break

        return result


    def parse_rows(self, rows):
        """
        Docstring for parse_rows

        :param rows: Description

        Columns : Date, Transaction Id, Remarks,
        """
        txns = []
        for row in rows:
            for rule in self.rules:
                is_match, index = rule.match(row)
                if is_match:
                    template = ss_transactions_template()

                    template['transaction_date'] = parse_date(row[index])
                    template['reference_id'] = row[1]
                    template['description'] = row[2]
                    template['entity_name'] = extract_entity_name(row[2])

                    template['amount'] = parse_amount(row[-2])
                    template['type'] = determine_transaction_type(row[-2])
                    template['payment_method'] = extract_payment_method(row[2])
                    txns.append(template)
        return txns

