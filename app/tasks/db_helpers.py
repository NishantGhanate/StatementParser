import os
import psycopg2


def _get_conn():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PWD"),
        host=os.getenv("DB_SERVER"),
        port=os.getenv("DB_PORT"),
    )


def save_metadata(metadata: dict) -> int | None:
    if not metadata:
        return None

    conn = _get_conn()
    cur = conn.cursor()

    sql = """
            INSERT INTO bank_info (
            bank_name,
            account_holder_name,
            account_number,
            account_type,
            cif_id,
            currency
        ) VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (account_number)
        DO UPDATE SET
            bank_name = EXCLUDED.bank_name
        RETURNING id;
        """

    cur.execute(
        sql,
        (
            metadata["bank_name"],
            metadata["account_holder_name"],
            metadata["account_number"],
            metadata["account_type"],
            metadata["cif_id"],
            metadata["currency"],
        ),
    )

    statement_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return statement_id


def save_transactions(transactions: list[dict]):
    conn = _get_conn()
    cur = conn.cursor()

    sql = """
    INSERT INTO bank_transactions (
        statement_id,
        reference_id,
        transaction_date,
        description,
        amount,
        currency,
        transaction_type,
        payment_method,
        category_id,
        tag_id,
        type_id,
        payment_method_id
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (reference_id, transaction_date, amount)
    DO NOTHING;
    """

    for tx in transactions:
        cur.execute(
            sql,
            (
                tx.get("statement_id"),
                tx["reference_id"],
                tx["transaction_date"],
                tx["description"],
                tx["amount"],
                tx.get("currency", "INR"),
                tx["transaction_type"],
                tx.get("payment_method"),
                tx.get("category_id"),
                tx.get("tag_id"),
                tx.get("type_id"),
                tx.get("payment_method_id"),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()
