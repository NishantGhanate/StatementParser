"""
Load up settings config for project, single point of config

> source .env
> python ./app/config/settings.py
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Environment(str, Enum):
    """
    Each env has use case
    on production logging debug will be auto disabled
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(str, Enum):
    """
    Pre-defined database types which is supported
    """

    POSTGRES = "postgres"
    MSSQL = "mssql"
    MYSQL = "mysql"
    STAR_ROCKS = "star_rocks"


class Settings(BaseSettings):
    """
    Loads ups config for service
    It loads attributes in given order
    """

    # model_config = SettingsConfigDict(
    #     env_file=BASE_DIR / ".env",  # Explicit path
    #     env_file_encoding="utf-8",
    #     extra="ignore",
    #     case_sensitive=True
    # )

    NAME: str = "StatementParser"
    ENVIRONMENT: Environment
    NOTIFY_EMAILS: Optional[List[str]]= None
    TIMEZONE: str = "Asia/Kolkata"

    # DB config
    DATABASE_TYPE: DatabaseType
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DB_DRIVER: Optional[str] = None
    SQL_DATABASE_URL: Optional[str] = None  # Build field
    SQL_DATABASE_CONFIG: Optional[dict] = None

    # Background process
    CELERY_USE_DB: bool = False
    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str
    CELERY_DEFAULT_QUEUE: str = "statement_q"

    # Genral cache
    REDIS_URL: str


    @field_validator("NOTIFY_EMAILS", mode="before")
    @classmethod
    def parse_emails(cls, v):
        """
        Parse emails from string to list
        """
        if isinstance(v, str):
            return [email.strip() for email in v.split(",")]
        return v

    @field_validator("CELERY_BACKEND_URL", mode="after")
    @classmethod
    def build_celery_backend_url(cls, v, values):
        """
        Build celery backend url based on CELERY_USE_DB flag.
        """
        data = values.data
        if not data.get("CELERY_USE_DB"):
            return v  # Use provided value or None

        db_type = data.get("DATABASE_TYPE")
        db_user = data.get("DATABASE_USER")
        db_pwd = data.get("DATABASE_PASSWORD")
        db_server = data.get("DATABASE_HOST")
        db_port = data.get("DATABASE_PORT")
        db_name = data.get("DATABASE_NAME")
        db_driver = data.get("DB_DRIVER", "ODBC Driver 18 for SQL Server")

        if not all([db_type, db_user, db_pwd, db_server, db_port, db_name]):
            raise ValueError("Missing required DB configuration for Celery backend URL")

        pwd_encoded = quote_plus(db_pwd)
        db_url = ""
        if db_type == "mssql":
            driver_encoded = quote_plus(db_driver)
            db_url = (
                f"db+mssql+pyodbc://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"
                f"?TrustServerCertificate=yes&driver={driver_encoded}"
            )
        elif db_type == "postgres":
            db_url = f"db+sqlalchemy://postgresql://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"  # pylint: disable=line-too-long
        elif db_type == "mysql":
            db_url = f"db+sqlalchemy://mysql+pymysql://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"  # pylint: disable=line-too-long
        else:
            raise ValueError(f"Unsupported DATABASE_TYPE: {db_type}")

        return db_url

    @model_validator(mode="after")
    def build_urls(self):
        # Build SQL_DATABASE_URL
        db_type = self.DATABASE_TYPE
        db_user = self.DATABASE_USER
        db_pwd = self.DATABASE_PASSWORD
        db_server = self.DATABASE_HOST
        db_port = self.DATABASE_PORT
        db_name = self.DATABASE_NAME
        driver = self.DB_DRIVER

        pwd_encoded = quote_plus(db_pwd)

        if db_type == DatabaseType.MSSQL:
            self.SQL_DATABASE_URL = (
                f"mssql+pyodbc://{db_user}:{pwd_encoded}@{db_server},{db_port}/{db_name}"
                f"?TrustServerCertificate=yes&driver={quote_plus(driver or 'ODBC Driver 18 for SQL Server')}"
            )
        elif db_type == DatabaseType.POSTGRES:
            self.SQL_DATABASE_URL = f"postgresql://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"
        elif db_type == DatabaseType.MYSQL:
            self.SQL_DATABASE_URL = f"mysql+pymysql://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"
        else:
            raise ValueError(f"Unsupported DATABASE_TYPE: {db_type}")

        # Build SQL_DATABASE_CONFIG
        self.SQL_DATABASE_CONFIG = {
            "server": db_server,
            "database": db_name,
            "username": db_user,
            "password": pwd_encoded,
        }

        # Build CELERY_BACKEND_URL if using DB
        if self.CELERY_USE_DB:
            if db_type == DatabaseType.MSSQL:
                self.CELERY_BACKEND_URL = (
                    f"db+mssql+pyodbc://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"
                    f"?TrustServerCertificate=yes&driver={quote_plus(driver or 'ODBC Driver 18 for SQL Server')}"
                )
            elif db_type == DatabaseType.POSTGRES:
                self.CELERY_BACKEND_URL = f"db+postgresql://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"
            elif db_type == DatabaseType.MYSQL:
                self.CELERY_BACKEND_URL = f"db+mysql+pymysql://{db_user}:{pwd_encoded}@{db_server}:{db_port}/{db_name}"

        return self

    @field_validator("SQL_DATABASE_CONFIG", mode="before")
    @classmethod
    def build_sql_database_config(cls, _, values):
        """
        Return dict
        """
        data = values.data

        db_user = data.get("DATABASE_USER")
        db_pwd = data.get("DATABASE_PASSWORD")
        db_server = data.get("DATABASE_HOST")
        db_port = data.get("DATABASE_PORT")
        db_name = data.get("DATABASE_NAME")
        driver = data.get("DB_DRIVER", 'Not set')

        pwd_encoded = quote_plus(db_pwd)

        sql_config = {
            "server": db_server,
            "database": db_name,
            "username": db_user,
            "password": pwd_encoded,
        }

        return sql_config


settings = Settings()

if __name__ == "__main__":
    settings = Settings()
    # print(settings.NOTIFY_EMAILS)
    # print(settings.DATABASE_URL)
    print(settings.CELERY_BACKEND_URL)
