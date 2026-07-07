"""Local-disk storage for uploaded dataset CSVs.

Files live under {UPLOAD_DIR}/datasets/{dataset_id}/ with a generated
stored_filename so two uploads can never collide, even with the same
original name.
"""

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset_file import DatasetFile
from app.services.exceptions import InvalidUploadError

# Browsers are inconsistent about the MIME type they send for CSVs.
ALLOWED_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel"}


def validate_upload(upload: UploadFile) -> None:
    """Reject anything that is not a CSV upload."""
    filename = upload.filename or ""
    if not filename.lower().endswith(".csv"):
        raise InvalidUploadError(f"Only CSV files are accepted; got {filename!r}")
    if upload.content_type and upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidUploadError(
            f"Only CSV files are accepted; got content type {upload.content_type!r}"
        )


def save_dataset_file(db: Session, dataset_id: int, upload: UploadFile) -> DatasetFile:
    """Validate the upload, write it to disk, and record a DatasetFile row."""
    validate_upload(upload)

    stored_filename = f"{uuid4().hex}.csv"
    directory = Path(settings.UPLOAD_DIR) / "datasets" / str(dataset_id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / stored_filename

    try:
        with open(path, "wb") as destination:
            shutil.copyfileobj(upload.file, destination)

        file = DatasetFile(
            dataset_id=dataset_id,
            original_filename=upload.filename,
            stored_filename=stored_filename,
            file_path=str(path),
            file_size=path.stat().st_size,
            content_type=upload.content_type,
        )
        db.add(file)
        db.commit()
    except Exception:
        # Don't leave orphaned files on disk if the write or insert fails.
        path.unlink(missing_ok=True)
        raise

    db.refresh(file)
    return file
