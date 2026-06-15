from pydantic import BaseModel
from app.schemas.common import TimeStampRead


class DatasetBase(BaseModel):
    name: str
    description: str | None = None
    file_name: str | None = None


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    file_name: str | None = None


class DatasetRead(DatasetBase, TimeStampRead):
    id: int