from typing import Optional


class LayoutDetector:
    """
    Read-only layout detection.
    Used ONLY for routing & logging.
    """

    @staticmethod
    def detect(text: str) -> Optional[str]:
        t = (text or "").upper()

        # SBI
        if "STATE BANK OF INDIA" in t:
            return "SBI_V1"

        # HDFC
        if "HDFC BANK" in t:
            return "HDFC_TEXT"
        
        # ICICI — table layout
        if "ICICI BANK" in t and "STATEMENT OF TRANSACTIONS" in t:
            return "ICICI_TABLE"

        # UNION — TABLE layout
        if "WITHDRAWAL" in t and "DEPOSIT" in t and "BALANCE" in t:
            return "UNION_TABLE"

        # UNION — TEXT layout
        if "AMOUNT(RS.)" in t and ("(DR)" in t or "(CR)" in t):
            return "UNION_TEXT"
        
        


        return None
