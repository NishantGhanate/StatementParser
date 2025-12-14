
# """
# > source .env
# > python ./app/core/database.py
# """

# from contextlib import contextmanager

# import pyodbc
# from celery.backends.database.session import ResultModelBase
# from sqlalchemy import create_engine, text

# # from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import declarative_base, sessionmaker

# from app.config.settings import settings



# # For sync
# sync_engine = create_engine(
#     url=settings.SQL_DATABASE_URL,
#     pool_size=50,  # number of connections to keep in the pool
#     max_overflow=100,  # extra connections beyond pool_size
#     pool_timeout=30,  # seconds to wait before giving up
#     pool_recycle=1800,  # recycle connections after 30 minutes
#     echo=True,  # set to True for SQL logging
# )

# SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)
# session = SyncSessionLocal()

# Base = declarative_base()


# def get_sql_odbc_connection() -> pyodbc.Connection:  # pylint: disable=c-extension-no-member
#     """
#     Returns single connection
#     """
#     conn_str = (
#         f"DRIVER={settings.DB_DRIVER};"
#         f"SERVER={settings.DB_SERVER},{settings.DB_PORT};"
#         f"DATABASE={settings.DB_NAME};"
#         f"UID={settings.DB_USER};"
#         f"PWD={settings.DB_PWD};"
#         "TrustServerCertificate=yes"
#     )
#     conn = pyodbc.connect(conn_str)
#     return conn


# async def async_init_celery_tables(async_engine) -> None:
#     """
#     Optional : for async engine
#     Create Celery's result tables using the async engine.
#     """
#     async with async_engine.begin() as conn:
#         await conn.run_sync(ResultModelBase.metadata.create_all)


# def init_celery_tables_sync(engine) -> None:
#     """
#     Create Celery's result tables using the sync SQLAlchemy engine.
#     """
#     with engine.begin() as conn:
#         ResultModelBase.metadata.create_all(bind=conn)


# @contextmanager
# def get_sync_db():
#     """
#     Sync DB connection generator
#     """
#     db = SyncSessionLocal()
#     try:
#         yield db
#     except Exception:
#         db.rollback()
#         raise
#     finally:
#         db.close()


# def dispose_engine():
#     """
#     Dispose the async engine (closes pools and physical connections).
#     """
#     sync_engine.dispose()


# # For testing connection
# if __name__ == "__main__":

#     def test_odbc_connection():
#         """Validate db connection"""
#         try:
#             conn = get_sql_odbc_connection()
#             cursor = conn.cursor()
#             cursor.execute("SELECT 1")
#             result = cursor.fetchone()
#             assert result[0] == 1
#             print("ODBC connection test passed.")
#             conn.close()
#         except Exception as e:
#             print(f"ODBC connection test failed: {e}")

#     def test_db_connection():
#         """
#         Validate via sql alcmey
#         """
#         try:
#             with get_sync_db() as db:
#                 # Simple query to test connection
#                 result = db.execute(text("SELECT 1"))
#                 print("Connection successful:", result.scalar())
#         except Exception as e:
#             print("ODBC connection test failed:", e)

#     test_odbc_connection()
#     test_db_connection()




