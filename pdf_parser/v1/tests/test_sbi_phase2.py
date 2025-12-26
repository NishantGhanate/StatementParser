from pdf_parser.v1.orchestrator import parse_statement


def test_sbi_phase2_regression():
    txns = parse_statement("tests/fixtures/sbi.pdf")
    assert len(txns) == 72

    # spot-check first credit/debit behavior
    assert any(t["transaction_type"] == "credit" for t in txns)
    assert any(t["transaction_type"] == "debit" for t in txns)
