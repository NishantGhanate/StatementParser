"""
Read-only bank detection.
Does NOT influence routing or parsing.
Used only for visibility/logging.
"""
from typing import Optional


class BankDetector:
    """
    Detect bank name from header text.
    """

    @staticmethod
    def detect(text: str) -> Optional[str]:
        """
        Args:
            text (str): Extracted PDF text
        Returns:
            str | None: Bank name if detected
        """
        t = (text or "").upper()

        if "STATE BANK OF INDIA" in t or "SBI" in t:
            return "SBI"

        if "HDFC BANK" in t:
            return "HDFC"

        if "UNION BANK OF INDIA" in t:
            return "UNION"

        return None
