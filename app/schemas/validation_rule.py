from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ValidationRuleBase(BaseModel):
    name: str
    rule_type: str # examples: "not_null", "unique", "range_check", "format_check"

class ValidationRuleCreate(ValidationRuleBase):
    pass

class ValidationRuleUpdate(BaseModel):
    name: str | None = None
    rule_type: str | None = None

class ValidationRuleRead(ValidationRuleBase):
    id: int
    dataset_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)