from pydantic import BaseModel

from app.schemas.common import RuleType, TimeStampRead

class ValidationRuleBase(BaseModel):
    name: str
    rule_type: RuleType
    column_name: str | None = None
    params: dict | None = None
    is_active: bool = True
    

class ValidationRuleCreate(ValidationRuleBase):
    pass

class ValidationRuleUpdate(BaseModel):
    name: str | None = None
    rule_type: RuleType | None = None
    column_name: str | None = None
    params: dict | None = None
    is_active: bool | None = None

class ValidationRuleRead(ValidationRuleBase, TimeStampRead):
    id: int
    dataset_id: int