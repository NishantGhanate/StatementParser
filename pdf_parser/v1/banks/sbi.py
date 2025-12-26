"""
SBI bank parser registry.
"""
from typing import List
from pdf_parser.v1.rules.sbi_rules import SbiTxnRowRule
from pdf_parser.v1.rules.base import Rule


class SbiBank:
    """
    SBI v1 rule registry.
    """
    bank_name = "SBI"
    rules: List[Rule] = [
        SbiTxnRowRule(),
    ]
