from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_run_by_id_or_404, get_error_or_404
from app.db.session import get_db
from app.models.validation_error import ValidationError
from app.schemas.validation_error import ValidationErrorCreate, ValidationErrorRead

router = APIRouter(prefix="/runs/{run_id}/errors", tags=["Validation Errors"])


@router.post("", response_model=ValidationErrorRead, status_code=status.HTTP_201_CREATED)
def create_error(run_id: int, data: ValidationErrorCreate, db: Session = Depends(get_db)):
    """
    Record a validation error against a run.

    Input:  run_id (path), ValidationErrorCreate (message, column_name, rule_id, rule_type_snapshot)
    Output: ValidationErrorRead
    Raises: 404 if run not found
    """
    get_run_by_id_or_404(db, run_id)
    error = ValidationError(
        run_id=run_id,
        message=data.message,
        column_name=data.column_name,
        rule_id=data.rule_id,
        rule_type_snapshot=data.rule_type_snapshot
    )
    db.add(error)
    db.commit()
    db.refresh(error)
    return error


@router.get("", response_model=list[ValidationErrorRead])
def list_errors(run_id: int, db: Session = Depends(get_db)):
    """
    Return all validation errors for a run.

    Input:  run_id (path)
    Output: list of ValidationErrorRead
    Raises: 404 if run not found
    """
    get_run_by_id_or_404(db, run_id)
    return db.query(ValidationError).filter(ValidationError.run_id == run_id).all()


@router.get("/{error_id}", response_model=ValidationErrorRead)
def get_error(run_id: int, error_id: int, db: Session = Depends(get_db)):
    """
    Return a single validation error by ID.

    Input:  run_id (path), error_id (path)
    Output: ValidationErrorRead
    Raises: 404 if run or error not found
    """
    return get_error_or_404(db, run_id, error_id)


@router.delete("/{error_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_error(run_id: int, error_id: int, db: Session = Depends(get_db)):
    """
    Delete a validation error.

    Input:  run_id (path), error_id (path)
    Output: 204 No Content
    Raises: 404 if run or error not found
    """
    error = get_error_or_404(db, run_id, error_id)
    db.delete(error)
    db.commit()