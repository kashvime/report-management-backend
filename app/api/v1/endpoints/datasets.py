from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetRead
from app.api.v1.dependencies import get_dataset_or_404
from app.schemas.validation_run import ValidationRunSummary
from app.services.exceptions import DatasetNotFoundError, DatasetNotRunnableError, RuleConfigError
from app.services.validation_engine import run_validation

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(data: DatasetCreate, db: Session = Depends(get_db)):
    """
    Create a new dataset.

    Input:  DatasetCreate (name, optional description)
    Output: DatasetRead
    """
    dataset = Dataset(**data.model_dump())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)):
    """
    Return all datasets.

    Output: list of DatasetRead
    """
    return db.query(Dataset).all()


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Return a single dataset by ID.

    Input:  dataset_id (path)
    Output: DatasetRead
    Raises: 404 if not found
    """
    return get_dataset_or_404(db, dataset_id)


@router.patch("/{dataset_id}", response_model=DatasetRead)
def update_dataset(dataset_id: int, data: DatasetUpdate, db: Session = Depends(get_db)):
    """
    Partially update a dataset.

    Input:  dataset_id (path), DatasetUpdate (any subset of name, description)
    Output: DatasetRead with updated fields
    Raises: 404 if not found
    """
    dataset = get_dataset_or_404(db, dataset_id)

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(dataset, field, value)

    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Delete a dataset and all its dependent rules and runs.

    Input:  dataset_id (path)
    Output: 204 No Content
    Raises: 404 if not found
    """
    dataset = get_dataset_or_404(db, dataset_id)
    db.delete(dataset)
    db.commit()

@router.post(
    "/{dataset_id}/run-validation",
    response_model=ValidationRunSummary,
    tags=["Validation Runs"],
)
def run_dataset_validation(dataset_id: int, db: Session = Depends(get_db)):
    """
    Run all active validation rules for the dataset.

    Input:  dataset_id (path)
    Output: ValidationRunSummary with run details and error counts
    Raises: 404 if dataset not found, 422 if dataset is not runnable or rules are misconfigured
    """
    try:
        return run_validation(db, dataset_id)

    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except (DatasetNotRunnableError, RuleConfigError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )