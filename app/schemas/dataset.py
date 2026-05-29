from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DatasetBase(BaseModel):
    name: str
    description: str | None = None


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DatasetRead(DatasetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)