from typing import List, Dict
import pdfplumber
import re

from pdf_parser.v1.core.transaction_builder import build_transaction


ROW_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\((DR|CR)\)\s*(\d+(?:\.\d+)?)\s*\(CR\)",
    re.IGNORECASE,
)

DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")

NOISE_TOKENS = ("@ok", "@yb", "@ap", "/SBIN/", "/HDFC/", "/ICIC/", "/UTIB/")


def _clean_description(lines: list[str]) -> str:
    text = " ".join(l.strip() for l in lines if l.strip())
    for tok in NOISE_TOKENS:
        text = text.replace(tok, "")
    return " ".join(text.split())


def parse_union_text(pdf_path: str) -> List[Dict]:
    transactions: List[Dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = text.splitlines()
    rows = list(ROW_RE.finditer(text))
    dates = DATE_RE.findall(text)

    count = min(len(rows), len(dates))

    for i in range(count):
        amt, dc, _ = rows[i].groups()
        start = rows[i].start()

        desc_lines = []
        for line in reversed(lines):
            if line in text[:start] and line.strip():
                desc_lines.append(line)
                if len(desc_lines) == 2:
                    break

        description = _clean_description(reversed(desc_lines))

        transactions.append(
            build_transaction(
                dates[i],
                description,
                amt,
                "debit" if dc.upper() == "DR" else "credit",
                entity_name=None,
            )
        )

    return transactions
