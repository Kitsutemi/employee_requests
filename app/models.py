from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)

    authored_requests = relationship(
        "Request", foreign_keys="Request.author_id", back_populates="author"
    )
    executed_requests = relationship(
        "Request", foreign_keys="Request.executor_id", back_populates="executor"
    )


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    author_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    executor_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="new")

    __table_args__ = (
        CheckConstraint("status IN ('new','in_progress','done')", name="check_status"),
        Index(
            "idx_requests_executor_status_deadline",
            "executor_id",
            "status",
            "deadline",
        ),
    )

    author = relationship("Employee", foreign_keys=[author_id], back_populates="authored_requests")
    executor = relationship("Employee", foreign_keys=[executor_id], back_populates="executed_requests")