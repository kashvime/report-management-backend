from datetime import datetime
from pydantic import BaseModel

from app.schemas.common import RunStatus, TimeStampRead

class ValidationRunUpdate(BaseModel):
    status: RunStatus | None = None

class ValidationRunRead(TimeStampRead):
    id: int
    dataset_id: int
    #The uploaded file the run is being executed against. Null if the run was triggered without a file.
    file_id: int | None = None
    status: RunStatus
    # Populated once the run reaches a terminal state; null while pending/running.
    total_records_checked: int | None = None
    total_errors_found: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None

class ValidationRunSummary(BaseModel):
    """Result returned by the run-validation endpoints."""
    run_id: int
    dataset_id: int
    file_id: int | None = None
    status: RunStatus
    total_records_checked: int | None = None
    total_errors_found: int | None = None
    errors_by_rule: dict[str, int]
    
class ValidationRunReport(BaseModel):
    """Result returned by GET /validation-runs/{run_id}/summary."""
    run_id: int
    dataset_name: str
    file_name: str | None = None
    status: RunStatus
    total_records_checked: int | None = None
    total_errors_found: int | None = None
    failure_reason: str | None = None
    errors_by_rule_type: dict[str, int]
    errors_by_field: dict[str, int]
