from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone
from app.db.base import Base


class ValidationRule(Base):
    """
    ValidationRule defines a rule that can be applied to a dataset to check its quality.
    
    Each rule belongs to one dataset and is reused across multiple validation runs.
    """
    __tablename__ = "validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # examples: "not_null", "unique", "range_check", "format_check"
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="rules")

    errors: Mapped[list["ValidationError"]] = relationship(
        "ValidationError",
        back_populates="rule",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ValidationRule id={self.id} name={self.name!r} type={self.rule_type!r}>"