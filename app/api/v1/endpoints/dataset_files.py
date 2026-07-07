from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_dataset_or_404, get_file_or_404
from app.db.session import get_db
from app.models.dataset_file import DatasetFile
from app.schemas.dataset_file import DatasetFileRead
from app.schemas.validation_run import ValidationRunSummary
from app.services.exceptions import (
    DatasetNotFoundError,
    DatasetNotRunnableError,
    InvalidUploadError,
    RuleConfigError,
)
from app.services.file_storage import save_dataset_file
from app.services.validation_engine import run_validation

router = APIRouter(prefix="/datasets/{dataset_id}/files", tags=["Dataset Files"])


@router.post("", response_model=DatasetFileRead, status_code=status.HTTP_201_CREATED)
def upload_file(dataset_id: int, file: UploadFile, db: Session = Depends(get_db)):
    """
    Upload a CSV file for a dataset.

    Input:  dataset_id (path), file (multipart form upload)
    Output: DatasetFileRead
    Raises: 404 if dataset not found, 400 if the file is not a CSV
    """
    get_dataset_or_404(db, dataset_id)
    try:
        return save_dataset_file(db, dataset_id, file)
    except InvalidUploadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("", response_model=list[DatasetFileRead])
def list_files(dataset_id: int, db: Session = Depends(get_db)):
    """
    Return all uploaded files for a dataset.

    Input:  dataset_id (path)
    Output: list of DatasetFileRead
    Raises: 404 if dataset not found
    """
    get_dataset_or_404(db, dataset_id)
    return db.query(DatasetFile).filter(DatasetFile.dataset_id == dataset_id).all()


@router.get("/{file_id}", response_model=DatasetFileRead)
def get_file(dataset_id: int, file_id: int, db: Session = Depends(get_db)):
    """
    Return a single uploaded file by ID.

    Input:  dataset_id (path), file_id (path)
    Output: DatasetFileRead 
    Raises: 404 if dataset or file not found
    """
    return get_file_or_404(db, dataset_id, file_id)


@router.post(
    "/{file_id}/run-validation",
    response_model=ValidationRunSummary,
    tags=["Validation Runs"],
)
def run_file_validation(dataset_id: int, file_id: int, db: Session = Depends(get_db)):
    """
    Run all active validation rules against an uploaded file.

    Input:  dataset_id (path), file_id (path)
    Output: ValidationRunSummary with run details and error counts
    Raises: 404 if dataset or file not found, 422 if the run fails
            (the failed run is kept with its failure_reason)
    """
    file = get_file_or_404(db, dataset_id, file_id)
    try:
        return run_validation(db, dataset_id, dataset_file=file)

    except DatasetNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))

    except (DatasetNotRunnableError, RuleConfigError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
