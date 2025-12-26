from decimal import Decimal, InvalidOperation
from dateutil import parser as date_parser


def _parse_amount(value):
    if not value:
        return None
    try:
        return Decimal(value.replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


def build_transaction(
    date_raw,
    description,
    amount_raw,
    transaction_type,      # "debit" | "credit"
    entity_name=None,
    person_id=1,
):
    amount = _parse_amount(amount_raw)
    if amount is None:
        raise ValueError("invalid_amount")

    return {
        "entity_name": entity_name,
        "transaction_date": date_parser.parse(date_raw, dayfirst=True).strftime("%Y-%m-%d"),
        "person_id": person_id,
        "type_id": None,
        "category_id": None,
        "tag_id": None,
        "amount": amount,
        "currency": "INR",
        "payment_method_id": None,
        "goal_id": None,
        "description": description.strip() if description else "",
        "remarks": None,
        "transaction_type": transaction_type,  
    }
