"""
Docstring for app.tasks.bank_statment_upload

> source venv/bin/activate
> source .env

> python app/tasks/bank_statement_upload.py --input files/union1_unlocked.pdf  --from_email noreplyunionbankofindia@unionbankofindia.bank.in --to_email nishant7.ng@gmail.com

"""

import logging

from app.core.database import fetch_all, fetch_one
from app.model_actions.bank_account import get_or_create_bank_account
from app.model_actions.transactions import bulk_insert_transactions
from app.pdf_normalizer.parser import parse_statement
from app.pdf_normalizer.utils import get_bank_from_email
from app.rule_engine.evaluator import TransactionCategorizer
from app.rule_engine.parser import parse
from celery import shared_task

logger = logging.getLogger("app")

@shared_task(
    bind=True,
    name='app.tasks.bank_statement_upload.process_bank_pdf',
    queue='statment_parser'
)
def process_bank_pdf(self, file_path: str, from_email: str, to_email: str):
    """
    This function binds logics togther.
    Gets bank name,
    """
    bank_name = get_bank_from_email(email= from_email)
    result = parse_statement(pdf_path=file_path, bank_name= bank_name)

    # call db and get user_id based on to_email from ss_users table
    user_obj = fetch_one(
        query="SELECT id FROM ss_users WHERE email = %s and is_active=true", params=(to_email,)
    )
    logger.debug(user_obj)

    # get rules from ss_categorization_rules for given user
    dsl_rules = fetch_all(
        "SELECT id, dsl_text FROM ss_categorization_rules WHERE user_id = %s and is_active=true",
        (user_obj['id'],)
    )
    logger.debug(f"Total {len(dsl_rules)} rules fetched for {from_email}")

    rules = []
    for data in dsl_rules:
        try:
            rules.append(parse(data['dsl_text']))
        except Exception:
            logger.exception(f"Failed to parse rule = {data}")

    # Load the rules
    categorizer = TransactionCategorizer(rules)

    # for transaction in result['transactions']:
    #     matching = categorizer.find_matching_rules(transaction)
    #     for rule in matching:
    #         logger.debug(f"  - {rule.name} (priority: {rule.priority})")


    applied_rule_tx = categorizer.categorize_batch(result['transactions'])
    # logger.debug(f'Total TX {len(applied_rule_tx)} after applying rules: {applied_rule_tx}')

    account_details, is_success = get_or_create_bank_account(
        user_id= user_obj['id'],
        number=result['account_details'].get('number'),
        ifsc_code=result['account_details'].get('ifsc_code'),
        account_type=result['account_details'].get('type')
    )
    if not is_success:
        raise Exception('Could find account details to link transcations')


    # Assign user id in txn
    for data in applied_rule_tx:
        data['user_id'] = user_obj['id']
        data['bank_account_id'] = account_details['id']


    stats = bulk_insert_transactions(transactions=applied_rule_tx)
    logger.info(f"Bulk insert stats = {stats}")

    result['transactions'] = applied_rule_tx
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract text")
    parser.add_argument("--input", required=True, help="Input PDF file path")
    parser.add_argument("--from_email", required=True, help="email sender")
    parser.add_argument("--to_email", required=True, help="email reciever")
    args = parser.parse_args()
    result = process_bank_pdf(file_path=args.input, from_email=args.from_email, to_email=args.to_email)

