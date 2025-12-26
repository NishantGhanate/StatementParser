from decimal import Decimal
from typing import Dict


def normalize_transaction(tx: Dict) -> Dict:
    tx = tx.copy()

    amount = tx.get("amount")
    try:
        amount = Decimal(amount)
    except Exception:
        amount = Decimal("0.00")

    tx_type = tx.get("transaction_type")

    if tx_type == "debit":
        tx["signed_amount"] = -amount
    elif tx_type == "credit":
        tx["signed_amount"] = amount
    else:
        tx["signed_amount"] = Decimal("0.00")

    tx["bank"] = tx.get("source_bank")
    tx["layout"] = tx.get("source_layout")

    return tx
