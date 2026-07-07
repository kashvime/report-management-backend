"""Validation engine: run a dataset's active rules against a CSV.

The CSV is either an uploaded DatasetFile or,
a sample file referenced by dataset.file_name.
"""

import csv
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_file import DatasetFile
from app.models.validation_error import ValidationError
from app.models.validation_rule import ValidationRule
from app.models.validation_run import ValidationRun
from app.schemas.common import RuleType, RunStatus
from app.schemas.validation_run import ValidationRunReport, ValidationRunSummary
from app.services.exceptions import (
    DatasetNotFoundError,
    DatasetNotRunnableError,
    RuleConfigError,
)
from app.services.rules import CHECKERS, matches_when
from app.utils import utc_now

SAMPLE_DATA_DIR = Path("sample_data")

def resolve_csv_path(dataset: Dataset, dataset_file: DatasetFile | None) -> Path:
    """Path of the CSV to validate: the uploaded file, or the sample fallback."""
    if dataset_file is not None:
        return Path(dataset_file.file_path)
    if not dataset.file_name:
        raise DatasetNotRunnableError(f"Dataset '{dataset.name}' has no CSV file configured")
    return SAMPLE_DATA_DIR / dataset.file_name

def load_csv(path: Path):
    """Read a CSV into (rows, header)."""
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

def run_validation(
    db: Session, dataset_id: int, dataset_file: DatasetFile | None = None
) -> ValidationRunSummary:
    """Run all active rules for the dataset, return a summary of the run.

    Validates the given uploaded file, or the dataset's sample CSV when no
    file is passed. The run moves pending -> running -> completed/failed;
    a failed run keeps its failure_reason and the original error is re-raised
    for the API layer to translate.
    """
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise DatasetNotFoundError(f"Dataset with id {dataset_id} not found")

    run = ValidationRun(
        dataset_id=dataset_id,
        file_id=dataset_file.id if dataset_file else None,
        status=RunStatus.PENDING,
    )
    db.add(run)
    db.commit()  # Need to commit to get an ID for the run

    run.status = RunStatus.RUNNING
    run.started_at = utc_now()
    db.commit()

    try:
        rows, header = load_csv(resolve_csv_path(dataset, dataset_file))

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
        run.completed_at = utc_now()
        db.commit()
    except Exception as exc:
        db.rollback()  # Discard any errors recorded before the failure
        run.status = RunStatus.FAILED
        run.failure_reason = str(exc)
        run.completed_at = utc_now()
        db.commit()
        raise

    return ValidationRunSummary(
        run_id=run.id,
        dataset_id=run.dataset_id,
        file_id=run.file_id,
        status=run.status,
        total_records_checked=run.total_records_checked,
        total_errors_found=run.total_errors_found,
        errors_by_rule=errors_by_rule,
    )


def count_errors_by(db: Session, run_id: int, column) -> dict[str, int]:
    """Count a run's errors grouped by the given ValidationError column."""
    counts = (
        db.query(column, func.count())
        .filter(ValidationError.run_id == run_id, column.isnot(None))
        .group_by(column)
        .all()
    )
    return dict(counts)

def build_run_report(db: Session, run: ValidationRun) -> ValidationRunReport:
    """Aggregate a run's errors into the report served by /validation-runs/{id}/summary."""
    file_name = run.file.original_filename if run.file else run.dataset.file_name
    return ValidationRunReport(
        run_id=run.id,
        dataset_name=run.dataset.name,
        file_name=file_name,
        status=run.status,
        total_records_checked=run.total_records_checked,
        total_errors_found=run.total_errors_found,
        failure_reason=run.failure_reason,
        errors_by_rule_type=count_errors_by(db, run.id, ValidationError.rule_type_snapshot),
        errors_by_field=count_errors_by(db, run.id, ValidationError.column_name),
    )
