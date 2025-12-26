from decimal import Decimal
from typing import List, Dict, Optional


def fix_hdfc_direction(transactions: List[Dict]) -> List[Dict]:
    fixed: List[Dict] = []
    prev_balance: Optional[Decimal] = None

    for tx in transactions:
        bal = tx.get("balance")

        if isinstance(bal, Decimal) and isinstance(prev_balance, Decimal):
            delta = bal - prev_balance
            if delta > 0:
                tx["transaction_type"] = "credit"
            elif delta < 0:
                tx["transaction_type"] = "debit"

        if isinstance(bal, Decimal):
            prev_balance = bal

        fixed.append(tx)

    return fixed
