
"""
Module contains
"""

import logging
import time
from functools import wraps

logger = logging.getLogger("app")


def log_start_end(func):
    """
    Decorator to time function excution
    """

    @wraps(func)
    def inner(*args, **kwargs):
        logger.info(f"Starting function: {func.__name__}")
        start_time = time.time()
        result = func(*args, **kwargs)

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"Finished function: {func.__name__} in {duration:.2f} seconds")
        return result

    return inner
