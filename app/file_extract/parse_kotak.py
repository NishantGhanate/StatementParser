"""
Docstring for app.file_extract.parse_kotak
> https://github.com/NishantGhanate/ExpenseBoard/blob/main/schema.sql

> python app/file_extract/parse_kotak.py files/15547619-XXXXXXX-400008_unlocked.pdf

> python app/file_extract/parse_kotak.py files/66XXXXX211_unlocked.pdf
"""


import argparse
import logging

import pdfplumber

from app.file_extract.values_extract import (determine_transaction_type,
                                             extract_entity_name, parse_amount,
                                             parse_date)

logger = logging.getLogger("app")

def normalize_transaction(row: dict, person_id: int) -> dict:
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
        'type': tx_type,
        'type_id': None,  # Lookup from ss_transaction_types based on tx_type
        'category_id': None,  # Needs categorization logic
        'tag_id': None,
        'payment_method_id': None,  # Could infer from UPI/NEFT/IMPS prefix
        'payment_method': tx_type,
        'amount': amount,
        'currency': 'INR',
        'goal_id': None,
        'description': details,
        'reference_id': row.get('cheque_reference', ''),
    }


def extract_table_to_dicts(pdf_path, person_id: int, password=None):
    open_kwargs = {"password": password} if password else {}

    all_rows = []
    headers = None

    with pdfplumber.open(pdf_path, **open_kwargs) as pdf:
        for page in pdf.pages:
            try:
                table = page.extract_table()

                if table:
                    if headers is None:
                        headers = [h.strip().lower().replace("/", "_").replace("#", "").replace(" ", "_") for h in table[0]]
                        data_rows = table[1:]
                    else:
                        data_rows = table[1:] if table[0] == headers else table

                    for row in data_rows:
                        try :
                            row_dict = {headers[i]: (cell.strip() if cell else "") for i, cell in enumerate(row)}
                            if 'opening' in row_dict.get('transaction_details').lower():
                                continue
                            normal_values = normalize_transaction(row= row_dict, person_id=person_id)
                            all_rows.append(normal_values)

                        except Exception:
                            logger.exception(f"parsing row failed : where row = {row}")

            except Exception:
                logger.exception(f"parsing table failed : where table = {table}")

    return all_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PDF table to list of dicts")
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("-p", "--password", help="PDF password (if protected)")

    args = parser.parse_args()

    rows = extract_table_to_dicts(pdf_path=args.input, person_id=1, password=args.password)

    for row in rows:
        print(row)
