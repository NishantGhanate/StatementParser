from pdf_parser.v1.rules.sbi_rules import SbiTxnRowRule


def test_sbi_rule_match():
    rule = SbiTxnRowRule()
    row = ["01-01-24", "ATM WDL", "", "500.00", "1000.00"]
    assert rule.match(row) is True
