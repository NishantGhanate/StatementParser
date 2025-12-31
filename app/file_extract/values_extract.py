import re
from decimal import Decimal

from dateutil import parser


def parse_amount(value: str) -> Decimal | None:
    """Parse amount string like '+20,000.00' or '-500.00' to Decimal"""
    if not value:
        return None
    cleaned = re.sub(r'[^\d.]', '', value)
    return Decimal(cleaned) if cleaned else None


def parse_date(date_str: str) -> str:
    """Parse various date formats to 'YYYY-MM-DD'"""
    dt = parser.parse(date_str.strip(), dayfirst=True)
    return dt.strftime("%Y-%m-%d")


def extract_entity_name(details: str) -> str | None:
    """Extract entity/person name from transaction details"""
    details = details.replace('\n', ' ')

    # UPI format: UPI/NAME/...
    if details.startswith('UPI/'):
        parts = details.split('/')
        if len(parts) >= 2:
            return parts[1].strip()

    # NEFT/IMPS format
    if details.startswith(('NEFT-', 'IMPS-')):
        match = re.search(r'(?:NEFT|IMPS)-[^-]+-([^-]+)', details)
        if match:
            return match.group(1).strip()

    return None


def determine_transaction_type(row: dict) -> str:
    """Return 'credit' or 'debit' based on which field has value"""
    if row.get('credit'):
        return 'credit'
    return 'debit'


def normalize_transaction(row: dict, person_id: int = 1) -> dict:
    """
    Normalize PDF extracted row to ss_transactions schema

    Args:
        row: Dict from PDF extraction
        person_id: ID of the person (from ss_persons table)

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
        'person_id': person_id,
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

    normalized = normalize_transaction(sample, person_id=1)

    for k, v in normalized.items():
        print(f"{k}: {v}")



def extract_entity_name(details: str) -> str | None:
    """Extract entity/person name from transaction details"""
    details = details.replace('\n', ' ')

    # UPI format: UPI/NAME/...
    if details.startswith('UPI/'):
        parts = details.split('/')
        if len(parts) >= 2:
            return parts[1].strip()

    # NEFT/IMPS format
    if details.startswith(('NEFT-', 'IMPS-')):
        match = re.search(r'(?:NEFT|IMPS)-[^-]+-([^-]+)', details)
        if match:
            return match.group(1).strip()

    return None

def determine_transaction_type(row: dict) -> str:
    """Return 'credit' or 'debit' based on which field has value"""
    if row.get('credit'):
        return 'credit'
    return 'debit'



