"""
Bank statement upload task
"""

from celery import shared_task

from app.common.enums import BankName
from app.pdf_normalizer.utils import get_bank_from_email
from app.pdf_normalizer.parser import parse_statement
from app.pdf_normalizer.metadata.union import parse_union_metadata

from app.rule_engine.adapters.transaction_adapter import adapt_transactions
from app.rule_engine.parser import parse_rules
from app.rule_engine.evaluator import TransactionCategorizer

from app.tasks.db_helpers import save_metadata, save_transactions


@shared_task(
    bind=True,
    name="app.tasks.bank_statement_upload.process_bank_pdf",
    queue="statement_parser",
)
def process_bank_pdf(self, file_path: str, from_email: str):
    # 1️⃣ Detect bank
    bank_name = get_bank_from_email(from_email)

    # 2️⃣ Parse statement (transactions + full text)
    transactions = parse_statement(
        pdf_path=file_path,
        bank_name=bank_name,
    )

    # 3️⃣ Extract metadata
    metadata = None
    if bank_name == BankName.UNION and transactions:
        metadata = parse_union_metadata(transactions[0]["_full_text"])

    # 4️⃣ Rules engine
    normalized = adapt_transactions(transactions)

    rules_dsl = """
    rule "UPI" where payment_method:eq:"UPI" assign payment_method_id:1 priority 10;
    rule "Debit" where _raw_type:eq:"debit" assign type_id:2 priority 20;
    rule "Credit" where _raw_type:eq:"credit" assign type_id:1 priority 20;

    rule "Transfer" where payment_method:eq:"UPI" and entity_name:nnull assign category_id:1 priority 30;
    rule "Food" where description:con:"Dominos":i or description:con:"Zomato":i or description:con:"Swiggy":i assign category_id:2 priority 40;
    rule "Bills" where description:con:"MCGM":i or description:con:"Electric":i or description:con:"Water":i or description:con:"Gas":i or description:con:"Bill":i assign category_id:3 priority 50;
    rule "Investment" where payment_method:eq:"NACH" assign category_id:4 priority 60;
    rule "Salary" where _raw_type:eq:"credit" and amount:gt:"50000" assign category_id:5 priority 70;
    rule "Large" where amount:gt:"50000" assign tag_id:1 priority 100;
    """

    rules = parse_rules(rules_dsl)
    categorizer = TransactionCategorizer(rules)
    enriched = categorizer.categorize_batch(normalized)

    # 5️⃣ Persist (FIXED)
    statement_id = save_metadata(metadata)

    for tx in enriched:
        tx["statement_id"] = statement_id

    save_transactions(enriched)

    return {
        "transactions": enriched,
        "metadata": metadata,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bank statement upload")
    parser.add_argument("--input", required=True)
    parser.add_argument("--from_email", required=True)
    args = parser.parse_args()

    output = process_bank_pdf.run(
        file_path=args.input,
        from_email=args.from_email,
    )

    print("BANK METADATA:", output["metadata"])
    print(f"Saved {len(output['transactions'])} transactions to DB")
