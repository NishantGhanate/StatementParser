from files.hdfc_minimal import parse_hdfc_v1

if __name__ == "__main__":
    pdf_path = "hdfc.pdf"  # your file

    transactions = parse_hdfc_v1(pdf_path)

    print(f"Total transactions parsed: {len(transactions)}")
    print("-" * 50)

    for txn in transactions[:10]:
        print(txn)
