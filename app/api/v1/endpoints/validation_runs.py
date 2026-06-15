from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import db
from app.api.v1.dependencies import get_dataset_or_404, get_run_or_404
from app.db.session import get_db
from app.models.validation_run import ValidationRun
from app.schemas.validation_run import ValidationRunUpdate, ValidationRunRead

router = APIRouter(prefix="/datasets/{dataset_id}/runs", tags=["Validation Runs"])


@router.post("", response_model=ValidationRunRead, status_code=status.HTTP_201_CREATED)
def create_run(dataset_id: int, db: Session = Depends(get_db)):
    """
    Create a new validation run for a dataset.

    Input:  dataset_id (path)
    Output: ValidationRunRead with status 'pending'
    Raises: 404 if dataset not found
    """
    get_dataset_or_404(db, dataset_id)
    run = ValidationRun(dataset_id=dataset_id)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("", response_model=list[ValidationRunRead])
def list_runs(dataset_id: int, db: Session = Depends(get_db)):
    """
    Return all validation runs for a dataset.

    Input:  dataset_id (path)
    Output: list of ValidationRunRead
    Raises: 404 if dataset not found
    """
    get_dataset_or_404(db, dataset_id)
    return db.query(ValidationRun).filter(ValidationRun.dataset_id == dataset_id).all()


@router.get("/{run_id}", response_model=ValidationRunRead)
def get_run(dataset_id: int, run_id: int, db: Session = Depends(get_db)):
    """
    Return a single validation run by ID.

    Input:  dataset_id (path), run_id (path)
    Output: ValidationRunRead
    Raises: 404 if dataset or run not found
    """
    return get_run_or_404(db, dataset_id, run_id)


@router.patch("/{run_id}", response_model=ValidationRunRead)
def update_run(dataset_id: int, run_id: int, data: ValidationRunUpdate, db: Session = Depends(get_db)):
    """
    Update the status of a validation run.

    Input:  dataset_id (path), run_id (path), ValidationRunUpdate (status)
    Output: ValidationRunRead with updated status
    Raises: 404 if dataset or run not found
    """
    run = get_run_or_404(db, dataset_id, run_id)

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(run, field, value)

    db.commit()
    db.refresh(run)
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(dataset_id: int, run_id: int, db: Session = Depends(get_db)):
    """
    Delete a validation run and all its errors.

    Input:  dataset_id (path), run_id (path)
    Output: 204 No Content
    Raises: 404 if dataset or run not found
    """
    run = get_run_or_404(db, dataset_id, run_id)
    db.delete(run)
    db.commit()