
""" "
Event based functions wrap things which you want to do when server boots up and boots down
"""

import logging


logger = logging.getLogger("app")


async def startup_events():
    """
    Add your fucntions here which needs to be trigger at fast api start
    """
    logger.info("[Startup] Initializing  serer.")
    # # Optional on celery upgrade it creates this tables



async def shutdown_events():
    """
    Add your fucntions here which needs to be trigger at fast api shutdown
    """
    logger.info("[Shutdown] Cleaning up.")
