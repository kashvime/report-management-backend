from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text
from datetime import datetime, timezone
from app.db.base import Base

class Dataset(Base): 
    """
    Dataset is the root entity of the system that is being checked for quality. 

    - Validation rules define expectations for a dataset
    - Validation runs track each time validation is executed
    - Validation errors are results of failed checks during runs

    If a dataset is deleted, all related rules and runs are also deleted.
    
    """
    __tablename__ = "datasets" 

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # One dataset can have many validation rules
    rules: Mapped[list["ValidationRule"]] = relationship(
        "ValidationRule", 
        back_populates="dataset", 
        cascade="all, delete-orphan") 
    
    # One dataset can have many validation runs
    runs: Mapped[list["ValidationRun"]] = relationship(
        "ValidationRun", 
        back_populates="dataset", 
        cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name!r}>"

