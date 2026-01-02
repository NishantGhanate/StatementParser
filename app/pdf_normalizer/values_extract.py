import re
from decimal import Decimal

from dateutil import parser
from app.common.enums import TrascationType
from app.common.constants import PAYMENT_METHODS


def parse_amount(value: str) -> Decimal | None:
    """Parse amount string like '+20,000.00' or '-500.00' to Decimal"""
    if not value:
        return None
    cleaned = re.sub(r'[^\d.]', '', value)
    return cleaned if cleaned else None


def parse_date(date_str: str) -> str:
    """Parse various date formats to 'YYYY-MM-DD'"""
    dt = parser.parse(date_str.strip(), dayfirst=True)
    return dt.strftime("%Y-%m-%d")




def determine_transaction_type(row: dict) -> str:
    """Return 'credit' or 'debit' based on which field has value"""
    tx_type = ''
    match = re.search(r'\b(Cr|Dr)\b', row, re.IGNORECASE)
    if match:
        tx_type = TrascationType.CREDIT.value if match.group(1).lower() == "cr" else TrascationType.DEBIT.value

    elif row.get('credit'):
        return 'credit'

    return tx_type


def extract_payment_method(details: str) -> str | None:
    """Extract payment method from transaction details."""
    details = details.replace('\n', ' ').strip().upper()
    return next((method for method, pattern in PAYMENT_METHODS.items() if re.search(pattern, details)), None)


def extract_entity_name(details: str) -> str | None:
    """Extract entity/person name from transaction details."""
    details = details.replace('\n', ' ').strip()

    # UPI variants (UPI, UPIAR, UPIAB, etc.)
    if details.upper().startswith('UPI'):
        match = re.search(r'/(?:DR|CR)/([^/]+)/', details, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        parts = details.split('/')
        if len(parts) >= 2:
            return parts[1].strip()

    # NEFT format
    if details.upper().startswith('NEFT'):
        match = re.search(r'NEFT-[^-]+-([^-]+)', details, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # IMPS format
    if details.upper().startswith('IMPS'):
        match = re.search(r'IMPS-[^-]+-([^-]+)', details, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # RTGS format
    if details.upper().startswith('RTGS'):
        match = re.search(r'RTGS-[^-]+-([^-]+)', details, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # NACH format (last value)
    if details.upper().startswith('NACH'):
        parts = details.split('/')
        if len(parts) >= 2:
            return parts[-1].strip()

    # RTNCHG format (second last value)
    if details.upper().startswith('RTNCHG'):
        parts = details.split('/')
        if len(parts) >= 4:
            return parts[-2].strip()

    # ACH format
    if details.upper().startswith('ACH'):
        parts = details.split('/')
        if len(parts) >= 2:
            return parts[-1].strip()

    return None

def normalize_transaction(row: dict, user_id: int = 1) -> dict:
    """
    Normalize PDF extracted row to ss_transactions schema

    Args:
        row: Dict from PDF extraction
        user_id: ID of the person (from ss_persons table)

    Returns:
        Dict matching ss_transactions columns
    """
    details = row.get('transaction_details', '').replace('\n', ' ')
    tx_type = determine_transaction_type(row)

    # Get amount from credit or debit field
    amount_str = row.get('credit') or row.get('debit') or ''
    amount = parse_amount(amount_str)

    return {
        'entity_name': extract_entity_name(details),
        'transaction_date': parse_date(row['date']),
        'user_id': user_id,
        'type_id': None,  # Lookup from ss_transaction_types based on tx_type
        'category_id': None,  # Needs categorization logic
        'tag_id': None,
        'amount': amount,
        'currency': 'INR',
        'payment_method_id': None,  # Could infer from UPI/NEFT/IMPS prefix
        'goal_id': None,
        'description': details,
        'reference_id': row.get('cheque_reference', ''),
        '_raw_type': tx_type,  # Helper field for type_id lookup
    }


if __name__ == "__main__":
    # Test with your sample row
    sample = {
        'date': '20 Nov, 2025',
        'transaction_details': 'UPI/NISHANT KANTI G/276509066224/Payment from\nPh',
        'cheque_reference': 'UPI-532462637529',
        'debit': '',
        'credit': '+20,000.00',
        'balance': '73,179.26'
    }

    normalized = normalize_transaction(sample, user_id=1)

    for k, v in normalized.items():
        print(f"{k}: {v}")



