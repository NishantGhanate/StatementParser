from decimal import Decimal


def adapt_transactions(transactions: list[dict]) -> list[dict]:
    adapted = []

    for tx in transactions:
        tx_type = tx.get("type")  # 'debit' / 'credit'

        adapted.append({
            **tx,

            # Required by rule engine
            "transaction_type": tx_type,
            "_raw_type": tx_type,

            # Ensure numeric comparison works
            "amount": Decimal(str(tx["amount"])) if tx.get("amount") is not None else None,
        })

    return adapted
