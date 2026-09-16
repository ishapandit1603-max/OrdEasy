"""
===========================================================
Upload API
-----------------------------------------------------------
Thin HTTP wrapper: saves the uploaded file, then hands it to
pipeline_service.process_file(), which is the same function
the email-ingestion scheduler uses. This keeps "what happens
to a file" in exactly one place.
===========================================================
"""

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.services.database_service import get_db
from app.services.pipeline_service import process_file

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _save_upload(file: UploadFile) -> str:
    folder = {
        ".pdf": "pdfs",
        ".xlsx": "excel", ".xls": "excel", ".csv": "excel",
        ".png": "images", ".jpg": "images", ".jpeg": "images",
    }.get(Path(file.filename).suffix.lower(), "misc")

    save_dir = os.path.join(settings.UPLOAD_DIR, folder)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return save_path


@router.post("/upload")
async def upload_order(file: UploadFile = File(...), db: Session = Depends(get_db)):
    saved_path = _save_upload(file)
    return process_file(saved_path, db, source="manual_upload")
