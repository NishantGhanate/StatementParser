import pdfplumber

def extract_text(pdf_path: str) -> dict:
    text_chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

    full_text = "\n".join(text_chunks)

    # 🚨 SCANNED PDF GUARD (THIS IS NEW)
    if not full_text or len(full_text.strip()) < 50:
        return {
            "status": "no_text",
            "text": ""
        }

    return {
        "status": "ok",
        "text": full_text
    }
