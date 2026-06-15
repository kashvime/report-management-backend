from pydantic import BaseModel
from datetime import datetime
from app.schemas.common import ORMModel

class ValidationErrorBase(BaseModel):
    message: str
    column_name: str | None = None
    row_number: int | None = None
    rule_id: int | None = None
    # Plain str (not RuleType): a frozen record of the rule's type at the time
    # the error was raised, so it survives the rule being edited or deleted.
    rule_type_snapshot: str | None = None


class ValidationErrorCreate(ValidationErrorBase):
    # run_id comes from the path (POST /runs/{run_id}/errors).
    pass


class ValidationErrorRead(ValidationErrorBase, ORMModel):
    id: int
    run_id: int
    created_at: datetime