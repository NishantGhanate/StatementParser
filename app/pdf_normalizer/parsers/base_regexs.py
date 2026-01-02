import re

ROW_RE = re.compile(
    r"""
    (?P<date>\d{2}/\d{2}/\d{2})\s+
    (?P<desc>.+?)\s+
    (?P<ref>\d{6,})\s+
    (?P<valdt>\d{2}/\d{2}/\d{2})\s+
    (?P<debit>[\d,]+\.\d{2})?\s*
    (?P<credit>[\d,]+\.\d{2})?\s+
    (?P<balance>[\d,]+\.\d{2})
    """,
    re.VERBOSE,
)

DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}")

AMOUNT_RE = re.compile(r"-?[\d,]+\.\d{2}")
