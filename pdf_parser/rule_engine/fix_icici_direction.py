from decimal import Decimal
from typing import List, Dict


def fix_icici_direction(transactions: List[Dict]) -> List[Dict]:
    """
    Fix CREDIT / DEBIT for ICICI using balance delta.
    ICICI balances are always 'Cr' in statement.
    """

    fixed = []
    prev_balance: Decimal | None = None

    for tx in transactions:
        bal = tx.get("balance")

        if bal is not None and prev_balance is not None:
            delta = bal - prev_balance

            if delta > 0:
                tx["transaction_type"] = "credit"
                tx["amount"] = abs(tx["amount"])
            elif delta < 0:
                tx["transaction_type"] = "debit"
                tx["amount"] = abs(tx["amount"])

        prev_balance = bal if bal is not None else prev_balance
        fixed.append(tx)

    return fixed
