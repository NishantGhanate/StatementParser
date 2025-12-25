from decimal import Decimal
from typing import List, Dict


def fix_hdfc_direction(transactions: List[Dict]) -> List[Dict]:
    """
    Fix CREDIT / DEBIT using balance delta.
    This is the authoritative logic.
    """

    fixed = []
    prev_balance: Decimal | None = None

    for tx in transactions:
        bal = tx.get("balance")

        if bal is not None and prev_balance is not None:
            delta = bal - prev_balance
            if delta > 0:
                tx["transaction_type"] = "credit"
            elif delta < 0:
                tx["transaction_type"] = "debit"

        prev_balance = bal if bal is not None else prev_balance
        fixed.append(tx)

    return fixed
