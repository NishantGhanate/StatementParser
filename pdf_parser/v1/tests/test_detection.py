from pdf_parser.v1.detector.bank_detector import BankDetector
from pdf_parser.v1.banks.sbi import SbiBank


def test_sbi_bank_detection():
    text = "STATE BANK OF INDIA"
    detector = BankDetector([SbiBank])
    bank = detector.detect(text)
    assert bank is SbiBank
