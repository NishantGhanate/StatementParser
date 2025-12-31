"""
Api for documents ingestion
"""

import logging
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.api.v1 import PREFIX
from app.common.file_util import temp_dir
from app.tasks.bank_statement_upload import process_bank_pdf

logger = logging.getLogger(name="app")

file_upload_router = APIRouter(prefix=PREFIX)

MAX_SIZE_MB = 200  # optional size limit
CHUNK = 1024 * 1024 * 5  # 5 MB
CUSTOM_TEMP_DIR = temp_dir() / "temp" / "statements"
CUSTOM_TEMP_DIR.mkdir(parents=True, exist_ok=True)


class FileMeta(BaseModel):
    date: str | None = None
    subject: str | None = None
    from_email: str | None = None


@file_upload_router.post("/upload")
async def file_upload(
    file: UploadFile = File(...),
    subject: str = Form(None),
    from_email: str = Form(None),
    to_email: str = Form(None),
    date: str = Form(None)
):
    """
    Worker:
    - Waits on queue
    - Fetches file
    """

    try:
        logger.debug(f"Got meta : {from_email} {subject} {date}")
        size = 0

        suffix = Path(file.filename).suffix or ""
        temp_path = ""

        logger.debug(f"Saving file to {CUSTOM_TEMP_DIR}")
        with NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=str(CUSTOM_TEMP_DIR),
        ) as tmp:

            temp_path = tmp.name

            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > MAX_SIZE_MB * 1024 * 1024:
                    Path(temp_path).unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File too large. Max {MAX_SIZE_MB} MB",
                    )

                tmp.write(chunk)  # accumulate the file

            if size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty.",
                )

        # # content = await file.read()  # simple read op
        # # step 1: save the file
        task_obj = process_bank_pdf.apply_async(
            kwargs = {
                'file_path': temp_path,
                'from_email': from_email,
                'to_email' : to_email
            }
        )

        content = {
            "filename": file.filename,
            "subject": subject,
            "from_email": from_email,
            "date": date,
            'task_id': task_obj.id
        }

    except Exception as e:
        logger.exception("Upload failed")
        Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

    return JSONResponse(
        status_code=200,
        content={"message": "File uploaded and queued for processing", **content},
    )
