from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, true
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base
from app.utils import utc_now

class ValidationRule(Base):
    """
    ValidationRule defines a rule that can be applied to a dataset to check its quality.
    
    Each rule belongs to one dataset and is reused across multiple validation runs.
    """
    __tablename__ = "validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
   
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    column_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
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

    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="rules")

    errors: Mapped[list["ValidationError"]] = relationship(
        "ValidationError",
        back_populates="rule"
    )

    def __repr__(self) -> str:
        return f"<ValidationRule id={self.id} name={self.name!r} type={self.rule_type!r}>"