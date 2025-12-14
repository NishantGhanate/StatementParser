"""
Logger config

> python ./app/config/logger.py
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Any, Dict

import colorama
from colorama import Fore, Style

from app.config.settings import Environment, settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)


def get_logging_config(
    log_level: str = "INFO",
    log_dir="logs",
    log_format: str = "detailed",
    environment: str = "dev",
    max_file_size_mb: int = 15,
    backup_count: int = 10,
) -> Dict[str, Any]:
    """
    Build logger config
    """
    formats = {
        "simple": "%(levelname)s - %(name)s - %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
        "json": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
    }

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": formats["simple"], "datefmt": "%H:%M:%S"},
            "detailed": {"format": formats["detailed"], "datefmt": "%Y-%m-%d %H:%M:%S"},
            "json": {"format": formats["json"], "datefmt": "%Y-%m-%d %H:%M:%S"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": log_format,
                "stream": "ext://sys.stdout",
            },
            "file_root": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": log_format,
                "filename": str(log_dir / f"root_{environment}.log"),
                "maxBytes": max_file_size_mb * 1024 * 1024,
                "backupCount": backup_count,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "test_case": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "app": {"level": log_level, "handlers": ["console"], "propagate": False},
            "clean_up": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "celery_task": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        # "root": {"level": log_level, "handlers": ["console", "file_root"]},
    }

    # Add file handlers for each named logger
    for logger_name in config["loggers"]:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_filename = log_path / f"{logger_name}.log"

        handler_name = f"file_{logger_name.replace('.', '_')}"
        config["handlers"][handler_name] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": log_format,
            "filename": str(log_filename),
            "maxBytes": max_file_size_mb * 1024 * 1024,
            "backupCount": backup_count,
            "encoding": "utf-8",
        }
        config["loggers"][logger_name]["handlers"].append(handler_name)

    return config


def setup_logging(
    log_level: str = None,
    log_dir: str = "logs",
    log_format: str = "detailed",
    environment: str = None,
    enable_colors: bool = True,
    max_file_size_mb: int = 15,
    backup_count: int = 10,
) -> None:
    """
    Build's logger
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    if environment is None:
        environment = Environment.DEVELOPMENT.value

    config = get_logging_config(
        log_level=log_level,
        log_dir=log_dir,
        log_format=log_format,
        environment=environment,
        max_file_size_mb=max_file_size_mb,
        backup_count=backup_count,
    )
    logging.config.dictConfig(config)

    if enable_colors:
        colorama.init(autoreset=True)
        format_str = config["formatters"][log_format]["format"]
        datefmt = config["formatters"][log_format].get("datefmt")
        colored_formatter = ColoredFormatter(format_str, datefmt)

        for logger_name in config["loggers"]:
            logger = logging.getLogger(logger_name)
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setFormatter(colored_formatter)

        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(colored_formatter)

    _setup_noise_reduction()


def _setup_noise_reduction() -> None:
    noisy_loggers = [
        "faker",
        "urllib3",
        "requests",
        "psycopg2",
        "sqlalchemy",
        "matplotlib",
        "PIL",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Returns singleton logger objet"""
    return logging.getLogger(name)


def quick_setup(level: str = "INFO", enable_colors: bool = True) -> None:
    """quick only the fly use"""
    setup_logging(log_level=level, log_format="simple", enable_colors=enable_colors)


def setup_dev_logging() -> None:
    """logger show all"""
    setup_logging(
        log_level="DEBUG",
        log_format="detailed",
        environment="dev",
        enable_colors=True,
        max_file_size_mb=5,
        backup_count=5,
    )


def setup_test_logging() -> None:
    """logger only info and above"""
    setup_logging(
        log_level="INFO",
        log_format="simple",
        environment="test",
        enable_colors=False,
        max_file_size_mb=5,
        backup_count=3,
    )


def setup_prod_logging() -> None:
    """Prod logger only warning and above"""
    setup_logging(
        log_level="WARNING",
        log_format="detailed",
        environment="prod",
        enable_colors=False,
        max_file_size_mb=10,
        backup_count=10,
    )


def auto_setup() -> None:
    """
    Based on env setup logger
    """
    if settings.ENVIRONMENT == Environment.PRODUCTION:
        setup_prod_logging()
    else:
        setup_dev_logging()


if __name__ == "__main__":
    auto_setup()
    logger = get_logger("app")
    logger.info("Logging configuration test")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
