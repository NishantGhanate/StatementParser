
"""
Common Enums
"""

from enum import StrEnum


class FileType(StrEnum):
    """
    Based on file upload mark it csv or excel
    """

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"

class TranscationType(StrEnum):
    UPI = 'upi'
    IMPS = 'imps'
    NEFT = 'neft'
    ATM = 'atm'
    INTERNAL_TRANSFER = 'internal_transfer'
    CHEQUE = 'cheque'
    CASH = 'cash'


class BankName(StrEnum):
    UNION = 'union'
    KOTAK = 'kotak'
    HDFC = 'hdfc'

class TrascationType(StrEnum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    SELF_TRANSFER = 'self transfer'
