from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from app.db.base import Base
from app.utils import utc_now

class ValidationRun(Base):
    """
    ValidationRun represents a single execution of validation rules against a dataset.
    
    Runs belong to datasets and own their validation errors. Deleting
    a run cascades deletion to all associated errors.
    """
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # The uploaded file the run validated. Null for legacy sample-data runs,
    # and set to NULL if the file record is deleted so run history survives.
    file_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("dataset_files.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Lifecycle state of a validation execution
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )
    total_records_checked: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_errors_found: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="runs")

    file: Mapped["DatasetFile | None"] = relationship("DatasetFile", back_populates="runs")

    errors: Mapped[list["ValidationError"]] = relationship(
        "ValidationError",
        back_populates="run",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ValidationRun id={self.id} dataset_id={self.dataset_id} status={self.status!r}>"