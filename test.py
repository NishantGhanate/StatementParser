# test.py

from pdf_parser.extractor.pdf_text_extractor import extract_text
from pdf_parser.classifier.classifier import classify_pdf

# ===============================
# FIXERS
# ===============================
from pdf_parser.rule_engine.fix_hdfc_direction import fix_hdfc_direction
from pdf_parser.rule_engine.fix_icici_direction import fix_icici_direction

# ===============================
# SBI
# ===============================
from pdf_parser.layout_detector.sbi_layout_detector import detect_sbi_layout
from pdf_parser.parsers.sbi.parser_table_v1 import parse_sbi_table_v1
from pdf_parser.parsers.sbi.parser_table_v2 import parse_sbi_table_v2

# ===============================
# HDFC
# ===============================
from pdf_parser.parsers.hdfc.parser_table import parse_hdfc_table

# ===============================
# ICICI
# ===============================
from pdf_parser.parsers.icici.parser_table import parse_icici_table

# ===============================
# UNION
# ===============================
from pdf_parser.layout_detector.union_layout_detector import detect_union_layout
from pdf_parser.parsers.union.parser_table_v1 import parse_union_table_v1
from pdf_parser.parsers.union.parser_table_v2 import parse_union_table_v2

# ===============================
# Normalizer
# ===============================
from pdf_parser.rule_engine.normalize_transaction import normalize_transaction


CONFIDENCE_THRESHOLD = 0.6
MIN_ACCEPTABLE_TXNS = 50


def main(pdf_path: str):
    # -------------------------------------------------
    # STEP 1: Extract text
    # -------------------------------------------------
    extraction_result = extract_text(pdf_path)

    if extraction_result["status"] == "no_text":
        print("⚠️ Scanned PDF detected – OCR required")
        return

    text = extraction_result["text"]

    # -------------------------------------------------
    # STEP 2: Classification
    # -------------------------------------------------
    result = classify_pdf(text)

    print("\n=== CLASSIFICATION RESULT ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    if (
        result.get("doc_type") != "bank_statement"
        or result.get("confidence", 0) < CONFIDENCE_THRESHOLD
    ):
        print("\n❌ Parsing blocked")
        return

    bank = result.get("bank_name")
    transactions = []

    # -------------------------------------------------
    # STEP 3: ROUTING
    # -------------------------------------------------

    # ===============================
    # SBI
    # ===============================
    if bank == "SBI":
        print("\n🏦 Bank detected: SBI")

        layout_result = detect_sbi_layout(text)
        layout = layout_result["layout"]

        if layout == "SBI_TABLE_V1":
            transactions = parse_sbi_table_v1(
                text,
                person_id=1,
                statement_id="stmt_sbi_test",
            )

            if len(transactions) < MIN_ACCEPTABLE_TXNS:
                transactions = parse_sbi_table_v2(
                    pdf_path,
                    person_id=1,
                    statement_id="stmt_sbi_test",
                    raw_text=text,
                )

        elif layout == "SBI_TABLE_V2":
            transactions = parse_sbi_table_v2(
                pdf_path,
                person_id=1,
                statement_id="stmt_sbi_test",
                raw_text=text,
            )
        else:
            print("❌ Unsupported SBI layout")
            return

    # ===============================
    # HDFC
    # ===============================
    elif bank == "HDFC":
        print("\n🏦 Bank detected: HDFC")

        transactions = parse_hdfc_table(
            pdf_path,
            person_id=1,
            statement_id="stmt_hdfc_test",
        )

        transactions = fix_hdfc_direction(transactions)

    # ===============================
    # ICICI
    # ===============================
    elif bank == "ICICI":
        print("\n🏦 Bank detected: ICICI")

        transactions = parse_icici_table(
            pdf_path,
            person_id=1,
            statement_id="stmt_icici_test",
        )

        transactions = fix_icici_direction(transactions)

    # ===============================
    # UNION
    # ===============================
    elif bank == "UNION":
        print("\n🏦 Bank detected: UNION")

        layout = detect_union_layout(text)

        if layout == "UNION_TABLE_V1":
            transactions = parse_union_table_v1(
                pdf_path,
                person_id=1,
                statement_id="stmt_union_test",
            )

        elif layout == "UNION_TABLE_V2":
            transactions = parse_union_table_v2(
                pdf_path,
                person_id=1,
                statement_id="stmt_union_test",
            )

        else:
            print("❌ Unsupported UNION layout")
            return

    else:
        print(f"\n❌ Bank not supported yet: {bank}")
        return

    # -------------------------------------------------
    # STEP 4: NORMALIZATION
    # -------------------------------------------------
    print(f"\n=== NORMALIZED TRANSACTIONS ({len(transactions)}) ===")

    normalized_transactions = [
        normalize_transaction(tx) for tx in transactions
    ]

    for tx in normalized_transactions:
        print(tx)


if __name__ == "__main__":
    # main("sbi.pdf")
    # main("hdfc.pdf")
    # main("icici.pdf")
    # main("union.pdf")
    # main("union2.pdf")
    main("2.pdf")
