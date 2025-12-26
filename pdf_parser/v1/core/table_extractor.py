import pdfplumber

def extract_tables(pdf_path: str):
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                }
            ) or []

            for table in tables:
                for row in table:
                    if row and any(cell and cell.strip() for cell in row):
                        rows.append([cell.strip() if cell else "" for cell in row])

    return rows
