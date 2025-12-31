from pathlib import Path

ALLOWED_EXCEL_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".xlsb", ".xltx", ".xlt"}


def has_allowed_extension(file_name: str, extensions: set = {""}) -> bool:
    return any(file_name.lower().endswith(ext) for ext in extensions)


def is_excel_file(file_name: str) -> bool:
    return any(file_name.lower().endswith(ext) for ext in ALLOWED_EXCEL_EXTENSIONS)


def temp_dir():
    return Path(__file__).resolve().parents[2]

