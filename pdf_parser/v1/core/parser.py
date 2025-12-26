from typing import List, Dict
import pdfplumber

from pdf_parser.v1.core.table_extractor import extract_tables
from pdf_parser.v1.core.transaction_builder import build_transaction

from pdf_parser.v1.rules.sbi_rules import SbiTxnRowRule
from pdf_parser.v1.rules.icici_rules import IciciTxnRowRule

from pdf_parser.v1.banks.hdfc import parse_hdfc_v2
from pdf_parser.v1.banks.union.union_table import parse_union_table
from pdf_parser.v1.banks.union.union_text import parse_union_text
from pdf_parser.v1.banks.icici import parse_icici_table

from pdf_parser.v1.detector.bank_detector import BankDetector
from pdf_parser.v1.detector.layout_detector import LayoutDetector
from pdf_parser.v1.logging.parser_logger import log_row, log_output


def _extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _finalize(bank: str, layout: str, txns: List[Dict]) -> List[Dict]:
    """
    Single exit point for successful parsing.
    Logs final structured output and returns transactions.
    """
    log_row(
        "result",
        {
            "bank": bank,
            "layout": layout,
            "count": len(txns),
        },
    )

    log_output(
        status="ok",
        transactions=txns,
        meta={
            "bank": bank,
            "layout": layout,
        },
    )

    return txns


def parse_statement(pdf_path: str) -> List[Dict]:
    """
    v1 Parser Orchestrator (FROZEN)

    Routing priority (LOCKED):
    UNION_TABLE
    UNION_TEXT
    ICICI_TABLE
    HDFC_TEXT
    SBI_V1
    """

    text = _extract_text(pdf_path)

    detected_bank = BankDetector.detect(text)
    detected_layout = LayoutDetector.detect(text)

    log_row(
        "detect",
        {
            "detected_bank": detected_bank,
            "detected_layout": detected_layout,
        },
    )

    # =================================================
    # UNION — TABLE
    # =================================================
    if detected_layout == "UNION_TABLE":
        txns = parse_union_table(pdf_path)
        return _finalize("UNION", "UNION_TABLE", txns)

    # =================================================
    # UNION — TEXT
    # =================================================
    if detected_layout == "UNION_TEXT":
        txns = parse_union_text(pdf_path)
        return _finalize("UNION", "UNION_TEXT", txns)

    # =================================================
    # ICICI — TABLE
    # =================================================
    if detected_layout == "ICICI_TABLE":
        txns = parse_icici_table(pdf_path)
        return _finalize("ICICI", "ICICI_TABLE", txns)

    # =================================================
    # HDFC — TEXT EXCEPTION
    # =================================================
    if detected_layout == "HDFC_TEXT" or detected_bank == "HDFC":
        txns = parse_hdfc_v2(pdf_path)
        return _finalize("HDFC", "HDFC_TEXT", txns)

    # =================================================
    # SBI — TABLE + RULE ENGINE
    # =================================================
    if detected_layout == "SBI_V1" or detected_bank == "SBI":
        rows = extract_tables(pdf_path)
        rule = SbiTxnRowRule()

        txns = [
            build_transaction(**rule.extract(row))
            for row in rows
            if rule.match(row)
        ]

        return _finalize("SBI", "SBI_V1", txns)

    # =================================================
    # HARD FAIL — NO GUESSING
    # =================================================
    raise ValueError(
        f"Unsupported statement | bank={detected_bank} layout={detected_layout}"
    )
