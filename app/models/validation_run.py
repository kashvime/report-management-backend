from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone
from app.db.base import Base

class ValidationRun(Base):
    """
    ValidationRun represents a single execution of validation rules against a dataset.
    
    Each run is associated with exactly one dataset and can have multiple validation errors.
    If a dataset is deleted, all associated validation runs are also deleted.
    """
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # "pending", "running", "completed", "failed"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True) 

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="runs")

    errors: Mapped[list["ValidationError"]] = relationship(
        "ValidationError",
        back_populates="run",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ValidationRun id={self.id} dataset_id={self.dataset_id} status={self.status!r}>"