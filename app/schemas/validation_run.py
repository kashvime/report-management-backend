from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ValidationRunUpdate(BaseModel):
    status: str | None = None


class ValidationRunRead(BaseModel):
    id: int
    dataset_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)