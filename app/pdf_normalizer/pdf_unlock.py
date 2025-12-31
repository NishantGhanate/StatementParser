"""
Docstring for app.pdf_normalizer.pdf_unlock

> python app/pdf_normalizer/pdf_unlock.py files/XXXXXXXX.pdf -p XXXXX

> python app/pdf_normalizer/pdf_unlock.py files/XXXX-XXXXXXX.pdf -p XXXXX

> python app/pdf_normalizer/pdf_unlock.py files/union1.pdf -p XXXXXXXX
"""


import argparse

import pdfplumber
import pikepdf


def main():
    parser = argparse.ArgumentParser(description="Unlock and extract text from password-protected PDFs")
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("-p", "--password", required=True, help="PDF password")
    parser.add_argument("-o", "--output", help="Output unlocked PDF path (optional)")
    parser.add_argument("-t", "--text", action="store_true", help="Extract and print text")

    args = parser.parse_args()

    output_path = args.output or args.input.replace(".pdf", "_unlocked.pdf")

    # Unlock PDF
    with pikepdf.open(args.input, password=args.password) as pdf:
        pdf.save(output_path)
        print(f"Unlocked PDF saved to: {output_path}")

    # Extract text if requested
    if args.text:
        with pdfplumber.open(output_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                print(f"\n--- Page {i} ---\n{text}")


if __name__ == "__main__":
    main()
