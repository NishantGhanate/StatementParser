import logging
from typing import Any

from app.core.database import get_cursor

logger = logging.getLogger("app")

def get_or_create_bank_account(
    user_id: int,
    number: str,
    ifsc_code: str = None,
    account_type: str = None
) -> tuple[dict, bool]:
    """
    Get existing bank account or create new one.
    Returns (account_dict, created_bool)
    """

    try:
        with get_cursor() as cur:
            # Try to get existing
            cur.execute(
                "SELECT * FROM ss_bank_accounts WHERE number = %s",
                (number,)
            )
            row = cur.fetchone()

            if row:
                logger.debug("Bank account already exists")
                return dict(row), True

            # Create new
            cur.execute(
                """
                INSERT INTO ss_bank_accounts (user_id, number, ifsc_code, type)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (user_id, number, ifsc_code, account_type)
            )
            logger.debug("Bank account created")
            row = cur.fetchone()
            return dict(row), True

    except Exception as ex:

        logger.exception("Failed to get or create bank details")

        raise ex
