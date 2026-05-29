# Shared dependency functions for the v1 API layer.

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.validation_rule import ValidationRule
from app.models.validation_run import ValidationRun
from app.models.validation_error import ValidationError


def get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset not found")
    return dataset


def get_rule_or_404(db: Session, dataset_id: int, rule_id: int) -> ValidationRule:
    rule = db.get(ValidationRule, rule_id)
    if rule is None or rule.dataset_id != dataset_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validation rule not found")
    return rule


def get_run_or_404(db: Session, dataset_id: int, run_id: int) -> ValidationRun:
    run = db.get(ValidationRun, run_id)
    if run is None or run.dataset_id != dataset_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validation run not found")
    return run

def get_error_or_404(db: Session, run_id: int, error_id: int) -> ValidationError:
    error = db.get(ValidationError, error_id)
    if error is None or error.run_id != run_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validation error not found")
    return error

def get_run_by_id_or_404(db: Session, run_id: int) -> ValidationRun:
    run = db.get(ValidationRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validation run not found")
    return run
