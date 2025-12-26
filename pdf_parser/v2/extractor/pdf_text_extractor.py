import pdfplumber
from typing import Dict


def extract_text(pdf_path: str) -> Dict[str, str]:
    text_chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_chunks.append(page_text.strip())

    full_text = "\n".join(text_chunks)

    if not full_text or len(full_text) < 50:
        return {
            "status": "no_text",
            "text": "",
        }

    return {
        "status": "ok",
        "text": full_text,
    }
