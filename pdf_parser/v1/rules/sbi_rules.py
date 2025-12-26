"""
SBI v1 rules.

Phase-2 implementation that EXACTLY mirrors the proven
behavior from sbi_minimal.py (Phase-1).

No new logic. No inference. No structural assumptions.
"""
import re
from typing import Dict, List
from pdf_parser.v1.rules.base import Rule

DATE_RE = re.compile(r"\d{2}-\d{2}-\d{2}")
NUMERIC_RE = re.compile(r"^\d+(?:,\d+)*(?:\.\d{1,2})?$")


def _extract_entity_name(description: str) -> str | None:
    if not description:
        return None
    parts = description.split("/")
    if len(parts) >= 4:
        name = parts[3].strip()
        return name if name else None
    return None


class SbiTxnRowRule(Rule):
    """
    SBI transaction row rule (v1).

    Mirrors logic from sbi_minimal.sbi_row_parser exactly.
    """

    def match(self, row: List[str]) -> bool:
        if not row or len(row) < 2:
            return False
        return bool(row[0] and DATE_RE.match(row[0].strip()))

    def extract(self, row: List[str]) -> Dict:
        date_raw = row[0].strip()
        description = (row[1] or "").strip()
        desc_upper = description.upper()

        numeric_values = [
            cell
            for cell in row
            if cell and NUMERIC_RE.match(cell.replace(",", ""))
        ]

        if not numeric_values:
            raise ValueError("No numeric values found in SBI row")

        # amount = second last numeric (last is balance)
        amount_raw = (
            numeric_values[-2]
            if len(numeric_values) >= 2
            else numeric_values[0]
        )

        if "CR" in desc_upper:
            txn_type = "credit"
        elif "DR" in desc_upper:
            txn_type = "debit"
        elif "REF" in desc_upper:
            txn_type = "credit"
        else:
            txn_type = "debit"

        return {
            "date_raw": date_raw,
            "description": description,
            "amount_raw": amount_raw,
            "transaction_type": txn_type,
            "entity_name": _extract_entity_name(description),
        }
