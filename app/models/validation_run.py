from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey
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

    # Lifecycle state of a validation execution
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )

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

    errors: Mapped[list["ValidationError"]] = relationship(
        "ValidationError",
        back_populates="run",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ValidationRun id={self.id} dataset_id={self.dataset_id} status={self.status!r}>"