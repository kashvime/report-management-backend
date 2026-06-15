from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_dataset_or_404, get_rule_or_404
from app.db.session import get_db
from app.models.validation_rule import ValidationRule
from app.schemas.validation_rule import (
    ValidationRuleCreate,
    ValidationRuleUpdate,
    ValidationRuleRead,
)

router = APIRouter(prefix="/datasets/{dataset_id}/rules", tags=["Validation Rules"])


@router.post("", response_model=ValidationRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(dataset_id: int, data: ValidationRuleCreate, db: Session = Depends(get_db)):
    """
    Create a new validation rule for a dataset.

    Input:  dataset_id (path), ValidationRuleCreate (name, rule_type, optional column_name, params, is_active)
    Output: ValidationRuleRead
    Raises: 404 if dataset not found
    """
    get_dataset_or_404(db, dataset_id)
    rule = ValidationRule(dataset_id=dataset_id, **data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=list[ValidationRuleRead])
def list_rules(dataset_id: int, db: Session = Depends(get_db)):
    """
    Return all validation rules for a dataset.

    Input:  dataset_id (path)
    Output: list of ValidationRuleRead
    Raises: 404 if dataset not found
    """
    get_dataset_or_404(db, dataset_id)
    return db.query(ValidationRule).filter(ValidationRule.dataset_id == dataset_id).all()


@router.get("/{rule_id}", response_model=ValidationRuleRead)
def get_rule(dataset_id: int, rule_id: int, db: Session = Depends(get_db)):
    """
    Return a single validation rule by ID.

    Input:  dataset_id (path), rule_id (path)
    Output: ValidationRuleRead
    Raises: 404 if dataset or rule not found
    """
    return get_rule_or_404(db, dataset_id, rule_id)


@router.patch("/{rule_id}", response_model=ValidationRuleRead)
def update_rule(dataset_id: int, rule_id: int, data: ValidationRuleUpdate, db: Session = Depends(get_db)):
    """
    Partially update a validation rule.

    Input:  dataset_id (path), rule_id (path), ValidationRuleUpdate (any subset of name, rule_type)
    Output: ValidationRuleRead with updated fields
    Raises: 404 if dataset or rule not found
    """
    rule = get_rule_or_404(db, dataset_id, rule_id)

    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(dataset_id: int, rule_id: int, db: Session = Depends(get_db)):
    """
    Delete a validation rule.

    Input:  dataset_id (path), rule_id (path)
    Output: 204 No Content
    Raises: 404 if dataset or rule not found
    Past errors referencing this rule are preserved with rule_id set to NULL
    """
    rule = get_rule_or_404(db, dataset_id, rule_id)
    db.delete(rule)
    db.commit()