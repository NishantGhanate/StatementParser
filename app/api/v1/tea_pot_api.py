"""
Api for documents ingestion
"""

import logging

from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Form, Body
from fastapi.responses import JSONResponse

from app.api.v1 import PREFIX

logger = logging.getLogger(name="app")

tea_pot_router = APIRouter(prefix=PREFIX)




@tea_pot_router.post("/tea-pot")
async def file_upload(
    data: dict = Body(...)
):
    """
    Worker:
    - Waits on queue
    - Fetches file
    """

    try:

        task_obj = {}

    except Exception as e:
        logger.exception("Upload failed")


    return JSONResponse(
        status_code=200,
        content={"message": "File uploaded and queued for processing", **task_obj},
    )
