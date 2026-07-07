from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, true
from datetime import datetime
from app.db.base import Base
from app.utils import utc_now

class DatasetFile(Base):
    """
    DatasetFile represents one CSV uploaded for a dataset.

    Files belong to datasets and are deleted with them. 
    The original filename is stored for reference, 
    but the file is stored on disk with a unique name to avoid collisions.
    The file path and size are also stored, along with the content type if available. 
    Each file can have multiple validation runs associated with it.
    """
    __tablename__ = "dataset_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="files")

    runs: Mapped[list["ValidationRun"]] = relationship(
        "ValidationRun",
        back_populates="file"
    )

    def __repr__(self) -> str:
        return f"<DatasetFile id={self.id} dataset_id={self.dataset_id} original_filename={self.original_filename!r}>"
