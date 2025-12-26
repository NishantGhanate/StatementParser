from pdf_parser.v1.core.parser import parse_statement

print("Running ICICI test...")

txns = parse_statement("icici.pdf")

print("ICICI transactions:", len(txns))
print()

for i, t in enumerate(txns[:15], 1):
    print(i, t)
