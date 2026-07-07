from datetime import datetime

from app.schemas.common import ORMModel


class DatasetFileRead(ORMModel):
    """Metadata for an uploaded CSV. 
    Internal storage details such as the file path and generated filename
    stay server-side and are not exposed."""
    id: int
    dataset_id: int
    original_filename: str
    file_size: int
    content_type: str | None = None
    is_active: bool
    uploaded_at: datetime
