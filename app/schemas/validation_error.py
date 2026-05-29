from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ValidationErrorBase(BaseModel):
    message: str
    column_name: str | None = None
    rule_id: int | None = None
    rule_type_snapshot: str | None = None


class ValidationErrorCreate(ValidationErrorBase):
    # run_id comes from the path (POST /runs/{run_id}/errors).
    pass


class ValidationErrorRead(ValidationErrorBase):
    id: int
    run_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)