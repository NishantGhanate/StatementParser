"""
Example usage of the Transaction Categorizer POC.

> source .env
> python app/rule_engine/example.py

This demonstrates:
1. Parsing DSL rules
2. Evaluating rules against transactions
3. Complete categorization workflow
"""

from decimal import Decimal
from app.rule_engine.parser import parse, parse_rules
from app.rule_engine.evaluator import TransactionCategorizer, RuleEvaluator


def example_parse_single_rule():
    """Parse a single categorization rule."""
    print("=" * 60)
    print("EXAMPLE: Parse Single Rule")
    print("=" * 60)

    dsl = 'rule "Family Transfer" where entity_name:con:"KANTI":i and _raw_type:eq:"debit" assign category_id:1 tag_id:2 priority 10;'

    rule = parse(dsl)

    print(f"Rule Name: {rule.name}")
    print(f"Priority: {rule.priority}")
    print(f"Assignment: category_id={rule.assignment.category_id}, tag_id={rule.assignment.tag_id}")
    print()


def example_complete_categorization():
    """Complete categorization workflow."""
    print("=" * 60)
    print("EXAMPLE: Complete Categorization")
    print("=" * 60)

    rules_dsl = '''
    rule "Family - Kanti" where entity_name:con:"KANTI":i assign category_id:1 priority 10;
    rule "UPI Payment" where description:sw:"UPI/":i assign payment_method_id:1 priority 50;
    rule "Type - Credit" where _raw_type:eq:"credit" assign type_id:1 priority 200;
    rule "Type - Debit" where _raw_type:eq:"debit" assign type_id:2 priority 200;
    rule "Large Transaction" where amount:gt:"50000" assign tag_id:2 priority 100;
    '''

    rules = parse_rules(rules_dsl)
    categorizer = TransactionCategorizer(rules)

    transaction = {
        "entity_name": "KANTI RAMULU GA",
        "transaction_date": "2025-11-13",
        "person_id": 1,
        "type_id": None,
        "category_id": None,
        "tag_id": None,
        "amount": Decimal("75000.00"),
        "currency": "INR",
        "payment_method_id": None,
        "goal_id": None,
        "description": "UPI/KANTI RAMULU GA/531715436912/PaidViaKotakApp",
        "remarks": "UPI-531746164437",
        "_raw_type": "debit"
    }

    print("Input Transaction:")
    print(f"  entity_name: {transaction['entity_name']}")
    print(f"  amount: {transaction['amount']}")
    print(f"  description: {transaction['description']}")
    print(f"  _raw_type: {transaction['_raw_type']}")

    print("\nMatching Rules:")
    matching = categorizer.find_matching_rules(transaction)
    for rule in matching:
        print(f"  - {rule.name} (priority: {rule.priority})")

    result = categorizer.categorize(transaction)

    print("\nCategorized Result:")
    print(f"  category_id: {result['category_id']} (was None)")
    print(f"  tag_id: {result['tag_id']} (was None)")
    print(f"  type_id: {result['type_id']} (was None)")
    print(f"  payment_method_id: {result['payment_method_id']} (was None)")
    print()


def example_batch_categorization():
    """Categorize multiple transactions."""
    print("=" * 60)
    print("EXAMPLE: Batch Categorization")
    print("=" * 60)

    rules_dsl = '''
    rule "Family" where entity_name:con:"KANTI","RAMULU":i assign category_id:1 priority 10;
    rule "UPI" where description:sw:"UPI/":i assign payment_method_id:1 priority 50;
    rule "Credit" where _raw_type:eq:"credit" assign type_id:1 priority 100;
    rule "Debit" where _raw_type:eq:"debit" assign type_id:2 priority 100;
    rule "Large" where amount:gt:"50000" assign tag_id:2 priority 50;
    '''

    rules = parse_rules(rules_dsl)
    categorizer = TransactionCategorizer(rules)

    transactions = [
        {
            "entity_name": "KANTI RAMULU GA",
            "amount": Decimal("75000.00"),
            "description": "UPI/KANTI RAMULU GA/123/Payment",
            "_raw_type": "debit",
            "category_id": None, "tag_id": None, "type_id": None, "payment_method_id": None
        },
        {
            "entity_name": "SALARY EMPLOYER",
            "amount": Decimal("100000.00"),
            "description": "NEFT/SALARY/456",
            "_raw_type": "credit",
            "category_id": None, "tag_id": None, "type_id": None, "payment_method_id": None
        },
        {
            "entity_name": "AMAZON SELLER",
            "amount": Decimal("5000.00"),
            "description": "UPI/AMAZON/789/Purchase",
            "_raw_type": "debit",
            "category_id": None, "tag_id": None, "type_id": None, "payment_method_id": None
        },
    ]

    results = categorizer.categorize_batch(transactions)

    for i, (tx, result) in enumerate(zip(transactions, results)):
        print(f"Transaction {i+1}: {tx['entity_name']}")
        print(f"  category_id: {result['category_id']}")
        print(f"  tag_id: {result['tag_id']}")
        print(f"  type_id: {result['type_id']}")
        print(f"  payment_method_id: {result['payment_method_id']}")
        print()


def example_operators():
    """Demonstrate various operators."""
    print("=" * 60)
    print("EXAMPLE: Various Operators")
    print("=" * 60)

    evaluator = RuleEvaluator()

    # Contains with multiple values
    rule = parse('rule "test" where desc:con:"UPI","NEFT","IMPS":i assign category_id:1 priority 10;')
    transactions = [
        {"desc": "UPI/payment"},
        {"desc": "neft transfer"},
        {"desc": "CASH withdrawal"},
    ]
    print("Contains (UPI, NEFT, IMPS):")
    for tx in transactions:
        match = evaluator.evaluate_rule(rule, tx)
        print(f"  {tx['desc']:20} | {'✓' if match else '✗'}")

    # Between
    rule = parse('rule "test" where amount:between:"1000":"5000" assign category_id:1 priority 10;')
    transactions = [
        {"amount": Decimal("500")},
        {"amount": Decimal("1000")},
        {"amount": Decimal("3000")},
        {"amount": Decimal("5000")},
        {"amount": Decimal("6000")},
    ]
    print("\nBetween 1000-5000:")
    for tx in transactions:
        match = evaluator.evaluate_rule(rule, tx)
        print(f"  {tx['amount']:10} | {'✓' if match else '✗'}")

    # Regex
    rule = parse('rule "test" where desc:regex:"SALARY|PAYROLL":i assign category_id:1 priority 10;')
    transactions = [
        {"desc": "SALARY CREDIT"},
        {"desc": "PAYROLL TRANSFER"},
        {"desc": "Salary for June"},
        {"desc": "UPI PAYMENT"},
    ]
    print("\nRegex (SALARY|PAYROLL):")
    for tx in transactions:
        match = evaluator.evaluate_rule(rule, tx)
        print(f"  {tx['desc']:20} | {'✓' if match else '✗'}")
    print()


if __name__ == "__main__":
    example_parse_single_rule()
    example_complete_categorization()
    example_batch_categorization()
    example_operators()
