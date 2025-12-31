import re


def parse_union_metadata(text: str) -> dict:
    def find(pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else None

    return {
        "bank_name": "Union Bank of India",

        "account_holder_name": find(
            r"Name\s+([A-Z\s]+?)\s+Customer"
        ),

        "account_number": find(
            r"Account\s+Number\s+(\d{6,})"
        ),

        "account_type": find(
            r"Account\s+Type\s+([A-Za-z ]+Account)"


        ),

        "cif_id": find(
            r"Customer\/CIF\s+ID\s+(\d+)"
        ),

     

        "currency": find(
            r"Currency\s+([A-Z]{3})"
        ),
    }
