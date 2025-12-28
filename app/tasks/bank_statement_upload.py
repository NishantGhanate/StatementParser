"""
Docstring for app.tasks.bank_statment_upload

> source venv/bin/activate
> source .env

> python app/tasks/bank_statement_upload.py --input files/union1_unlocked.pdf  --from_email noreplyunionbankofindia@unionbankofindia.bank.in

"""


from app.pdf_normalizer.parser import parse_statement
from app.pdf_normalizer.utils import get_bank_from_email
from celery import shared_task



@shared_task(
    bind=True,
    name='app.tasks.bank_statement_upload.process_bank_pdf',
    queue='statment_parser'
)
def process_bank_pdf(self, file_path: str, from_email: str):
    bank_name = get_bank_from_email(email= from_email)

    result = parse_statement(pdf_path=file_path, bank_name= bank_name)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract text")
    parser.add_argument("--input", required=True, help="Input PDF file path")
    parser.add_argument("--from_email", required=True, help="email sender")
    args = parser.parse_args()
    result = process_bank_pdf(file_path=args.input, from_email=args.from_email)
    print(result)
