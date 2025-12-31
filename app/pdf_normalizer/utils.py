import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional
from app.common.enums import BANK_EMAIL_PATTERNS, BankName


def get_bank_identifier(pdf_path: str) -> str:
    """Read top half of first page to identify bank."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]

        # Get page dimensions
        height = page.height

        # Crop to top half: (x0, y0, x1, y1)
        top_half = page.crop((0, 0, page.width, height / 2))

        text = page.extract_text() or ""
        return text.lower()


def is_date_like(text: str) -> bool:
    """Check if text looks like a date."""
    if not text:
        return False
    # Matches formats like 01-11-25, 01/11/25, 01-11-2025, 16/05/2025
    return bool(re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', text.strip()))


def find_date_column(rows: list[list[str]]) -> int | None:
    """Auto-detect which column contains dates."""
    if not rows:
        return None

    num_cols = len(rows[0])

    for col_idx in range(num_cols):
        date_count = 0
        for row in rows[:10]:  # Check first 10 rows
            if col_idx < len(row) and is_date_like(row[col_idx]):
                date_count += 1

        # If most rows have a date in this column, it's the date column
        if date_count >= len(rows[:10]) // 2:
            return col_idx

    return None


def extract_table_rows(pdf_path: str) -> list[list[str]]:
    """Extract rows from tables that contain a date column."""
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.find_tables():
                data = table.extract()
                if not data:
                    continue

                # Find date column - skip table if none found
                date_col = find_date_column(data)
                if date_col is None:
                    continue

                expected_cols = len(data[0])
                pending_row = None

                for row in data:
                    if not row or not any(cell and cell.strip() for cell in row):
                        continue

                    cleaned = [cell.strip().replace('\n', ' ') if cell else "" for cell in row]

                    # Check if this is a complete row (has date)
                    has_date = is_date_like(cleaned[date_col]) if date_col < len(cleaned) else False

                    if has_date:
                        if pending_row:
                            all_rows.append(pending_row)
                        pending_row = cleaned
                    elif pending_row:
                        # Continuation row - merge
                        for i, cell in enumerate(cleaned):
                            if cell and i < len(pending_row):
                                if pending_row[i]:
                                    pending_row[i] += " " + cell
                                else:
                                    pending_row[i] = cell

                if pending_row:
                    all_rows.append(pending_row)

    return all_rows


def has_date_header(row: list[str]) -> int | None:
    """Check if row has a 'Date' column header. Returns column index or None."""
    if not row:
        return None

    for i, cell in enumerate(row):
        if cell and "date" in cell.lower().strip():
            return i

    return None


def is_date_like(text: str) -> bool:
    """Check if text looks like a date value."""
    if not text:
        return False
    text = text.strip()
    return bool(re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', text))

def has_date_header(row: list[str]) -> int | None:
    """Check if row has a 'Date' column header. Returns column index or None."""
    if not row:
        return None

    for i, cell in enumerate(row):
        if cell and "date" in cell.lower().strip():
            return i

    return None


def extract_table_rows(pdf_path: str) -> list[list[str]]:
    """Extract rows from tables that have a 'Date' column header."""
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.find_tables():
                data = table.extract()
                if not data or len(data) < 2:
                    continue

                # Check first few rows for date header
                date_col = None
                header_row_idx = None

                for idx, row in enumerate(data[:3]):
                    date_col = has_date_header(row)
                    if date_col is not None:
                        header_row_idx = idx
                        break

                # Skip table if no date header found
                if date_col is None:
                    continue

                pending_row = None

                # Process rows after header
                for row in data[header_row_idx + 1:]:
                    if not row or not any(cell and cell.strip() for cell in row):
                        continue

                    cleaned = [cell.strip().replace('\n', ' ') if cell else "" for cell in row]

                    # Check if this is a data row (has date value in date column)
                    has_date = is_date_like(cleaned[date_col]) if date_col < len(cleaned) else False

                    if has_date:
                        if pending_row:
                            all_rows.append(pending_row)
                        pending_row = cleaned
                    elif pending_row:
                        # Continuation row - merge
                        for i, cell in enumerate(cleaned):
                            if cell and i < len(pending_row):
                                if pending_row[i]:
                                    pending_row[i] += " " + cell
                                else:
                                    pending_row[i] = cell

                if pending_row:
                    all_rows.append(pending_row)

    return all_rows


def debug_tables(pdf_path: str):
    """See what pdfplumber is detecting."""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.find_tables()
            print(f"Page {page_num}: Found {len(tables)} table(s)")

            for i, table in enumerate(tables):
                data = table.extract()
                if data:
                    print(f"\n  Table {i+1}: {len(data)} rows, {len(data[0])} cols")
                    # Print first few rows to see structure
                    for j, row in enumerate(data[:5]):
                        print(f"    Row {j}: {len(row)} cols -> {row}")


def get_table_info(pdf_path: str):
    """Get table structure info including column count."""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.find_tables()  # Returns Table objects with metadata

            for i, table in enumerate(tables):
                # Get bounding box
                bbox = table.bbox  # (x0, y0, x1, y1)

                # Extract to count columns
                data = table.extract()
                if data:
                    num_cols = len(data[0])
                    num_rows = len(data)
                    print(f"Page {page_num}, Table {i+1}: {num_rows} rows × {num_cols} cols")
                    print(f"  Header: {data[0]}")


def _to_decimal(val: Optional[str]) -> Optional[Decimal]:
    if not val:
        return None
    try:
        return Decimal(val.replace(",", ""))
    except Exception:
        return None


def _to_date(val: str) -> Optional[str]:
    try:
        return datetime.strptime(val, "%d/%m/%y").date().isoformat()
    except Exception:
        return None


def _normalize_date(date_str: str) -> Optional[str]:
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date().isoformat()
        except Exception:
            continue
    return None


def account_details_dict():
    return {
        'number' : None,
        'ifsc_code' : None,
        'type' : None
    }

def transcation_dict():
    """
    Docstring for transform_dict

    :param kwargs: Try to match the schema
    """
    return {
        'entity_name': '',
        'transaction_date': '',
        'person_id': '',
        'type': '',
        'type_id': None,  # Lookup from ss_transaction_types based on tx_type
        'category_id': None,  # Needs categorization logic
        'tag_id': None,
        'payment_method_id': None,  # Could infer from UPI/NEFT/IMPS prefix
        'payment_method': '',
        'amount': '',
        'currency': 'INR',
        'goal_id': None,
        'description': '',
        'reference_id': '',
        'account_id': None
    }


def get_bank_from_email(email: str) -> BankName | None:
    """Determine bank from email address."""
    email = email.lower()
    return next((bank for bank, pattern in BANK_EMAIL_PATTERNS.items() if re.search(pattern, email)), None)


if __name__ == "__main__":
    pass
