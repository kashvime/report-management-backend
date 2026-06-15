"""Validation engine: run a dataset's active rules against its sample CSV."""

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.validation_error import ValidationError
from app.models.validation_rule import ValidationRule
from app.models.validation_run import ValidationRun
from app.schemas.common import RuleType, RunStatus
from app.schemas.validation_run import ValidationRunSummary
from app.services.exceptions import (
    DatasetNotFoundError,
    DatasetNotRunnableError,
    RuleConfigError,
)
from app.services.rules import CHECKERS, matches_when

SAMPLE_DATA_DIR = Path("sample_data")

def load_csv(dataset: Dataset):
    """Read the dataset's CSV into (rows, header)."""
    if not dataset.file_name:
        raise DatasetNotRunnableError(f"Dataset '{dataset.name}' has no CSV file configured")
    path = SAMPLE_DATA_DIR / dataset.file_name
    if not path.is_file():
        raise DatasetNotRunnableError(f"CSV file not found: {path}")
    with open(path, newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames or []

def get_active_rules(db: Session, dataset_id: int):
    """Get all active rules for the given dataset ID."""
    return (
        db.query(ValidationRule)
        .filter(ValidationRule.dataset_id == dataset_id, ValidationRule.is_active == True)
        .all()
    )

def evaluate_rule(rule: ValidationRule, rows, header):
    """Run one rule, raise RuleConfigError if the rule is misconfigured."""
    try:
        rule_type = RuleType(rule.rule_type)
    except ValueError:
        raise RuleConfigError(f"Unknown rule type: {rule.rule_type}")
    
    if not rule.column_name:
        raise RuleConfigError(f"Rule '{rule.name}' has no column_name")

    if rule.column_name not in header:
        raise RuleConfigError(f"Column {rule.column_name!r} is not in the CSV")

    failures = CHECKERS[rule_type](rows, rule.column_name, rule.params)
    when = (rule.params or {}).get("when")
    if when:
        failures = [f for f in failures if matches_when(rows[f.row_number - 2], when)]
    return failures

def run_validation(db: Session, dataset_id: int) -> ValidationRunSummary:
    """Run all active rules for the dataset, return a summary of the run."""
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise DatasetNotFoundError(f"Dataset with id {dataset_id} not found")
    
    rows, header = load_csv(dataset)
    
    run = ValidationRun(dataset_id=dataset_id, status=RunStatus.RUNNING)
    db.add(run)
    db.commit()  # Need to commit to get an ID for the run
    
    try:
        errors_by_rule = {}
        for rule in get_active_rules(db, dataset_id):
            failures = evaluate_rule(rule, rows, header)
            for failure in failures:
                db.add(
                    ValidationError(
                        run_id=run.id,
                        rule_id=rule.id,
                        rule_type_snapshot=rule.rule_type,
                        column_name=rule.column_name,
                        row_number=failure.row_number,
                        message=failure.message
                    )
                )
            if failures:
                errors_by_rule[rule.rule_type] = errors_by_rule.get(rule.rule_type, 0) + len(failures)
        run.total_errors_found = sum(errors_by_rule.values())
        run.total_records_checked = len(rows)
        run.status = RunStatus.COMPLETED
        db.commit()
    except Exception:
        db.rollback()
        run.status = RunStatus.FAILED
        db.commit()
        raise
    
    return ValidationRunSummary(
        run_id=run.id,
        dataset_id=run.dataset_id,
        status=run.status,
        total_records_checked=run.total_records_checked,
        total_errors_found=run.total_errors_found,
        errors_by_rule=errors_by_rule,
    )

