import re
import copy

from app.pdf_normalizer.parsers.base_parser import BankStatementParser
from app.pdf_normalizer.parsers.base_parsing_rules import DateAmountRule
from app.pdf_normalizer.utils import (
    account_details_dict,
    ss_transactions_template,
)
from app.pdf_normalizer.values_extract import (
    determine_transaction_type,
    extract_payment_method,
    parse_amount,
    parse_date,
)


class SBIBankParser(BankStatementParser):

    rules = [DateAmountRule()]
    bank_name = "SBI"

    # -------------------------------------------------
    # Detection
    # -------------------------------------------------
    def detect(self, text: str) -> bool:
        text = text.lower()
        return "state bank of india" in text or "sbi" in text

    # -------------------------------------------------
    # Account details
    # -------------------------------------------------
    def parse_account_details(self, text: str):
        result = account_details_dict()
        text_u = text.upper()

        # Account number (label-based)
        acc_match = re.search(
            r"(ACCOUNT\s+NUMBER|ACCOUNT\s+NO\.?|A/C\s+NO\.?)\s*[:\-]?\s*([X\d][X\d\s\-]{5,20})",
            text_u
        )
        if acc_match:
            result["number"] = acc_match.group(2).replace(" ", "").replace("-", "")

        # Fallback: masked account number anywhere (take LAST → transaction account)
        matches = re.findall(r"\bX{4,}\d{3,6}\b", text)
        if matches:
            result["number"] = matches[-1]

        # IFSC
        ifsc_match = re.search(r"\bSBIN0\d{6}\b", text_u)
        if ifsc_match:
            result["ifsc_code"] = ifsc_match.group(0)

        # Account type
        if "SAVING ACCOUNT" in text_u:
            result["type"] = "SAVINGS"
        elif "CURRENT ACCOUNT" in text_u:
            result["type"] = "CURRENT"

        return result

    # -------------------------------------------------
    # SBI entity extraction
    # -------------------------------------------------
    def extract_entity_from_description(self, description: str):
        if not description:
            return None

        # UPI format: UPI/DR/<ref>/<name>/<bank>/...
        parts = description.split("/")
        if len(parts) >= 4:
            name = parts[3].strip()
            if name and not name.isdigit():
                return name

        return None

    # -------------------------------------------------
    # SBI post processing
    # -------------------------------------------------
    def _sbi_post_process(self, txn: dict) -> dict:
        txn = txn.copy()
        desc = (txn.get("description") or "").upper()

        # UPI REF rows
        if desc.startswith("UPI/REF/"):
            txn["entity_name"] = None
            txn["payment_method"] = "UPI"

        # SBI service / renewal
        if desc.startswith("SBIYA") or "RENEWAL" in desc:
            txn["entity_name"] = "SBI"
            txn["payment_method"] = "SERVICE_CHARGE"

        # CASH deposits
        if "CASH DEPOSIT" in desc:
            txn["payment_method"] = "CASH"

        return txn

    # -------------------------------------------------
    # Transaction parsing
    # -------------------------------------------------
    def parse_rows(self, rows):
        """
        SBI row structure:
        [Date, Description, Ref, Credit, Debit, Balance]
        """
        seen = set()
        unique = []

        for row in rows:
            for rule in self.rules:
                is_match, index = rule.match(row)
                if not is_match:
                    continue

                template = copy.deepcopy(ss_transactions_template())

                # Date
                template["transaction_date"] = parse_date(row[index])

                # Description
                description = row[1] if len(row) > 1 else ""
                template["description"] = description

                # Entity
                entity = self.extract_entity_from_description(description)
                if entity and entity.isdigit():
                    entity = None
                template["entity_name"] = entity

                # Payment method
                template["payment_method"] = extract_payment_method(description)

                # Reference ID
                ref_match = re.search(r"UPI/(CR|DR)/(\d+)", description)
                template["reference_id"] = ref_match.group(2) if ref_match else None

                # Amount & type
                credit = row[-3] if len(row) >= 3 else ""
                debit = row[-2] if len(row) >= 2 else ""

                amount_source = credit if credit and credit != "-" else debit
                template["amount"] = parse_amount(amount_source)

                type_source = f"Cr {credit}" if credit and credit != "-" else f"Dr {debit}"
                template["type"] = determine_transaction_type(type_source)

                # SBI-specific cleanup
                template = self._sbi_post_process(template)

                # Dedup (SAFE: preserves same-day multiple txns)
                key = (
                    template["transaction_date"],
                    template["amount"],
                    template["description"],
                    template.get("reference_id"),
                )

                if key not in seen:
                    seen.add(key)
                    unique.append(template)

        return unique
