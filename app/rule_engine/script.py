"""
Docstring for app.rule_engine.script

> source .env
> pyhton app/rule_engine/script.py
"""
from app.rule_engine.evaluator import  TransactionCategorizer
from app.rule_engine.parser import parse_rules
from decimal import Decimal


category = {
    1 : 'Family',
    2 : 'Investment'
}

payment_method = {
    1 : 'UPI',
    2 : 'ATM'
}

tag = {
    1 : 'large',
    2 : 'small'
}

type = {
    1 : 'Credit',
    2 : 'Debit'
}

# Define rules
rules_dsl = '''
rule "Family Transfer" where entity_name:con:"KANTI":i assign category_id:1 priority 10;
rule "UPI Payment" where description:sw:"UPI/":i assign payment_method_id:1 priority 50;
rule "Large Transaction" where amount:gt:"50000" assign tag_id:2 priority 100;
rule "Debit Type" where _raw_type:eq:"debit" assign type_id:2 priority 200;
'''

# Parse and create categorizer
rules = parse_rules(rules_dsl)
categorizer = TransactionCategorizer(rules)

# Categorize a transaction
transaction = {
    "entity_name": "KANTI RAMULU GA",
    "description": "UPI/KANTI RAMULU GA/123/Payment",
    "_raw_type": "debit",
    "amount": Decimal("75000.00"),
    "category_id": None,
    "tag_id": None,
    "type_id": None,
    "payment_method_id": None,
}

result = categorizer.categorize(transaction)
print(category[result["category_id"]])       # 1 (Family)
print(payment_method[result["payment_method_id"]]) # 1 (UPI)
print(tag[result["tag_id"]])            # 2 (Large)
print(type[result["type_id"]])           # 2 (Debit)
