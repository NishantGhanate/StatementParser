
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
    UNION = "union"
    KOTAK = "kotak"
    SBI = "sbi"
    HDFC = "hdfc"
    ICICI = "icici"
    AXIS = "axis"
    PNB = "pnb"
    BOB = "bob"
    CANARA = "canara"
    IDBI = "idbi"
    YES = "yes"
    INDUSIND = "indusind"
    FEDERAL = "federal"


BANK_EMAIL_PATTERNS = {
    BankName.UNION: r"unionbank",
    BankName.KOTAK: r"kotak",
    BankName.SBI: r"sbi\.co\.in|@sbi\.",
    BankName.HDFC: r"hdfc",
    BankName.ICICI: r"icici",
    BankName.AXIS: r"axis",
    BankName.PNB: r"pnb|punjabnational",
    BankName.BOB: r"bankofbaroda|bob",
    BankName.CANARA: r"canara",
    BankName.IDBI: r"idbi",
    BankName.YES: r"yesbank",
    BankName.INDUSIND: r"indusind",
    BankName.FEDERAL: r"federal",
}

class TrascationType(StrEnum):
    CREDIT = 'credit'
    DEBIT = 'debit'
    SELF_TRANSFER = 'self transfer'
