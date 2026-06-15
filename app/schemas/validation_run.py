from pydantic import BaseModel

from app.schemas.common import RunStatus, TimeStampRead

class ValidationRunUpdate(BaseModel):
    status: RunStatus | None = None

class ValidationRunRead(TimeStampRead):
    id: int
    dataset_id: int
    status: RunStatus
    # Populated once the run reaches a terminal state; null while pending/running.
    total_records_checked: int | None = None
    total_errors_found: int | None = None

class ValidationRunSummary(BaseModel):
    """Result returned by POST /datasets/{dataset_id}/run-validation."""
    run_id: int
    dataset_id: int
    status: RunStatus
    total_records_checked: int | None = None
    total_errors_found: int | None = None
    errors_by_rule: dict[str, int]
    