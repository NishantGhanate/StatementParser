
"""
Common Enums
"""

from enum import StrEnum


class FileType(StrEnum):
    """
    Based on file upload mark it csv or excel
    """

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
