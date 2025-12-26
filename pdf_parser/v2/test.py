import json

from typing import List, Dict, Any

from pdf_parser.utils.logger import get_logger
from pdf_parser.extractor.pdf_text_extractor import extract_text
from pdf_parser.classifier.classifier import classify_pdf

from pdf_parser.rule_engine.fix_hdfc_direction import fix_hdfc_direction
from pdf_parser.rule_engine.fix_icici_direction import fix_icici_direction
from pdf_parser.rule_engine.normalize_transaction import normalize_transaction

from pdf_parser.layout_detector.sbi_layout_detector import detect_sbi_layout
from pdf_parser.layout_detector.union_layout_detector import detect_union_layout

from pdf_parser.parsers.sbi.parser_table_v1 import parse_sbi_table_v1
from pdf_parser.parsers.sbi.parser_table_v2 import parse_sbi_table_v2
from pdf_parser.parsers.hdfc.parser_table import parse_hdfc_table
from pdf_parser.parsers.icici.parser_table import parse_icici_table
from pdf_parser.parsers.union.parser_table_v1 import parse_union_table_v1
from pdf_parser.parsers.union.parser_table_v2 import parse_union_table_v2


logger = get_logger("PIPELINE")

CONFIDENCE_THRESHOLD = 0.6
MIN_ACCEPTABLE_TXNS = 5


def fail(reason: str) -> Dict[str, Any]:
    logger.error(reason)
    return {"status": "error", "reason": reason, "transactions": []}


def success(transactions: List[dict]) -> Dict[str, Any]:
    logger.info(f"Pipeline success | transactions={len(transactions)}")
    return {"status": "ok", "transactions": transactions}


def parse_by_bank(bank: str, text: str, pdf_path: str) -> Dict[str, Any]:
    transactions: List[dict] = []

    logger.info(f"Routing to bank parser: {bank}")

    # ===============================
    # SBI (V2 FIRST)
    # ===============================
    if bank == "SBI":
        logger.info("SBI → trying TABLE_V2 first")

        transactions = parse_sbi_table_v2(
            pdf_path,
            person_id=1,
            statement_id="stmt_sbi",
            raw_text=text,
        )

        if len(transactions) < MIN_ACCEPTABLE_TXNS:
            logger.info("SBI V2 low count → fallback to V1")

            layout_result = detect_sbi_layout(text)
            layout = layout_result.get("layout")
            logger.info(f"SBI layout detected: {layout}")

            if layout == "SBI_TABLE_V1":
                transactions = parse_sbi_table_v1(
                    text,
                    person_id=1,
                    statement_id="stmt_sbi",
                )
            else:
                return fail("Unsupported SBI layout")

    # ===============================
    # HDFC
    # ===============================
    elif bank == "HDFC":
        transactions = parse_hdfc_table(
            pdf_path,
            person_id=1,
            statement_id="stmt_hdfc",
        )
        transactions = fix_hdfc_direction(transactions)

    # ===============================
    # ICICI
    # ===============================
    elif bank == "ICICI":
        transactions = parse_icici_table(
            pdf_path,
            person_id=1,
            statement_id="stmt_icici",
        )
        transactions = fix_icici_direction(transactions)

    # ===============================
    # UNION
    # ===============================
    elif bank == "UNION":
        layout = detect_union_layout(text)
        logger.info(f"UNION layout detected: {layout}")

        if layout == "UNION_TABLE_V1":
            transactions = parse_union_table_v1(
                pdf_path,
                person_id=1,
                statement_id="stmt_union",
            )
        elif layout == "UNION_TABLE_V2":
            transactions = parse_union_table_v2(
                pdf_path,
                person_id=1,
                statement_id="stmt_union",
            )
        else:
            return fail("Unsupported UNION layout")

    else:
        return fail(f"Unsupported bank: {bank}")

    if not transactions:
        return fail("No transactions extracted")

    return success(transactions)


def main(pdf_path: str) -> Dict[str, Any]:
    logger.info(f"Starting pipeline for file: {pdf_path}")

    extract = extract_text(pdf_path)
    if extract.get("status") != "ok":
        return fail("No text extracted (OCR required)")

    text = extract["text"]
    classification = classify_pdf(text)

    logger.info(
        f"Classification → type={classification.get('doc_type')} "
        f"bank={classification.get('bank_name')} "
        f"confidence={classification.get('confidence')}"
    )

    if (
        classification.get("doc_type") != "bank_statement"
        or classification.get("confidence", 0) < CONFIDENCE_THRESHOLD
    ):
        return fail("Low confidence or not a bank statement")

    bank = classification.get("bank_name")
    parse_result = parse_by_bank(bank, text, pdf_path)

    if parse_result["status"] != "ok":
        return parse_result

    normalized = [normalize_transaction(tx) for tx in parse_result["transactions"]]

    result = success(normalized)

    # 🔴 LOG FULL PARSE OUTPUT AS JSON
    logger.info("PARSE_OUTPUT", extra={"payload": result})


    return result



if __name__ == "__main__":
    result = main("sbi.pdf")
    print(result)
