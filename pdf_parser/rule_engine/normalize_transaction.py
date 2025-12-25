from decimal import Decimal
from typing import Dict


def normalize_transaction(tx: Dict) -> Dict:
    """
    Ultra-minimal normalizer.
    No enrichment. No assumptions.
    """

    tx = tx.copy()

    if tx.get("transaction_type") == "debit":
        tx["signed_amount"] = -Decimal(tx["amount"])
    elif tx.get("transaction_type") == "credit":
        tx["signed_amount"] = Decimal(tx["amount"])
    else:
        tx["signed_amount"] = Decimal("0.00")

    tx["bank"] = tx.get("source_bank")
    tx["layout"] = tx.get("source_layout")

    return tx
