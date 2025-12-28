import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional

def extract_text(pdf_path: str) -> str:
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)

def extract_tables_as_plain_text(pdf_path):
    tables_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                text = "\n".join(
                    [" | ".join(cell or "" for cell in row) for row in table]
                )
                tables_text.append(text)

    return tables_text


def _to_decimal(val: Optional[str]) -> Optional[Decimal]:
    if not val:
        return None
    try:
        return Decimal(val.replace(",", ""))
    except Exception:
        return None


def _to_date(val: str) -> Optional[str]:
    try:
        return datetime.strptime(val, "%d/%m/%y").date().isoformat()
    except Exception:
        return None


def _normalize_date(date_str: str) -> Optional[str]:
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date().isoformat()
        except Exception:
            continue
    return None


def trasnsform_dict(**kwargs):

    return {
        'entity_name': '',
        'transaction_date': '',
        'person_id': '',
        'type': '',
        'type_id': None,  # Lookup from ss_transaction_types based on tx_type
        'category_id': None,  # Needs categorization logic
        'tag_id': None,
        'payment_method_id': None,  # Could infer from UPI/NEFT/IMPS prefix
        'payment_method': '',
        'amount': '',
        'currency': 'INR',
        'goal_id': None,
        'description': '',
        'reference_id': '',
    }
