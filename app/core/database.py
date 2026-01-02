"""
Reusable PostgreSQL database module using psycopg3
> pip install psycopg[binary,pool]
> python ./app/core/database.py
"""

from contextlib import contextmanager
from typing import Any, Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config.settings import settings

# Connection pool (thread-safe, reuses connections)
pool = ConnectionPool(
    conninfo=settings.SQL_DATABASE_URL,  # postgresql://user:pass@host:port/db
    min_size=5,
    max_size=50,
    timeout=10,
    max_idle=300,  # close idle connections after 5 min
)


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a connection from the pool."""
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor(dict_results: bool = True) -> Generator[psycopg.Cursor, None, None]:
    """Get a cursor with automatic connection handling."""
    row_factory = dict_row if dict_results else None
    with get_connection() as conn:
        with conn.cursor(row_factory=row_factory) as cur:
            yield cur


def execute(query: str, params: tuple | dict | None = None) -> None:
    """Execute a query (INSERT, UPDATE, DELETE)."""
    with get_cursor() as cur:
        cur.execute(query, params)


def fetch_one(query: str, params: tuple | dict | None = None) -> dict | None:
    """Fetch a single row as dict."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def fetch_all(query: str, params: tuple | dict | None = None) -> list[dict]:
    """Fetch all rows as list of dicts."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_val(query: str, params: tuple | dict | None = None) -> Any:
    """Fetch a single value."""
    with get_cursor(dict_results=False) as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return row[0] if row else None


def execute_many(query: str, params_list: list[tuple | dict]) -> None:
    """Execute query with multiple parameter sets (bulk insert/update)."""
    with get_cursor() as cur:
        cur.executemany(query, params_list)


def execute_returning(query: str, params: tuple | dict | None = None) -> dict | None:
    """Execute INSERT/UPDATE with RETURNING clause."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def close_pool() -> None:
    """Close all connections in the pool."""
    pool.close()


# --- Testing ---
if __name__ == "__main__":

    def test_connection():
        """Test basic connectivity."""
        result = fetch_val("SELECT 1")
        assert result == 1
        print("✓ Connection test passed")

    def test_fetch_all():
        """Test fetching multiple rows."""
        rows = fetch_all("SELECT table_name FROM information_schema.tables LIMIT 5")
        print(f"✓ Fetched {len(rows)} tables")

    def test_parameterized():
        """Test parameterized queries."""
        result = fetch_one("SELECT %s AS name, %s AS value", ("test", 123))
        assert result["name"] == "test"
        assert result["value"] == 123
        print("✓ Parameterized query test passed")

    def test_named_params():
        """Test named parameters."""
        result = fetch_one(
            "SELECT %(name)s AS name, %(value)s AS value",
            {"name": "hello", "value": 456}
        )
        assert result["name"] == "hello"
        print("✓ Named parameters test passed")

    # Run tests
    test_connection()
    test_fetch_all()
    test_parameterized()
    test_named_params()

    close_pool()
