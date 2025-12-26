from typing import Dict, List
from decimal import Decimal
import re


class IciciTxnRowRule:
    """
    ICICI TABLE layout
    Columns:
    Date | Particulars | Chq.No | Withdrawals | Deposits | Balance
    """

    DATE_RE = re.compile(r"\d{2}-\d{2}-\d{4}")

    def match(self, row: List[str]) -> bool:
        if not row or len(row) < 6:
            return False
        if not self.DATE_RE.match(row[0] or ""):
            return False
        return True

    def extract(self, row: List[str]) -> Dict | None:
        date = row[0].strip()
        description = row[1].strip() if row[1] else ""

        withdrawal = row[3].replace(",", "").strip() if row[3] else ""
        deposit = row[4].replace(",", "").strip() if row[4] else ""

        if withdrawal:
            try:
                if Decimal(withdrawal) > 0:
                    return {
                        "date_raw": date,
                        "description": description,
                        "amount_raw": withdrawal,
                        "transaction_type": "debit",
                    }
            except Exception:
                return None

        if deposit:
            try:
                if Decimal(deposit) > 0:
                    return {
                        "date_raw": date,
                        "description": description,
                        "amount_raw": deposit,
                        "transaction_type": "credit",
                    }
            except Exception:
                return None

        return None
