from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Employee, Request


class RequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, request_id: int) -> Optional[Request]:
        return self.db.query(Request).filter(Request.id == request_id).first()

    def get_last(self) -> Optional[Request]:
        return self.db.query(Request).order_by(Request.id.desc()).first()

    def create(self, request: Request) -> Request:
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def save(self, request: Request) -> Request:
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_filtered(
        self,
        *,
        status: Optional[str] = None,
        executor_id: Optional[int] = None,
        department: Optional[str] = None,
        overdue: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]:
        query = self.db.query(Request).options(
            joinedload(Request.author),
            joinedload(Request.executor),
        )

        if status:
            query = query.filter(Request.status == status)
        if executor_id:
            query = query.filter(Request.executor_id == executor_id)
        if department:
            query = query.join(Request.executor).filter(Employee.department == department)
        if overdue:
            query = query.filter(
                Request.deadline < datetime.utcnow(),
                Request.status != "done",
            )

        total = query.count()
        items = (
            query.order_by(Request.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def list_api(
        self,
        *,
        status: Optional[str] = None,
        executor_id: Optional[int] = None,
        department: Optional[str] = None,
        overdue: bool = False,
    ) -> list[Request]:
        query = self.db.query(Request)
        if status:
            query = query.filter(Request.status == status)
        if executor_id:
            query = query.filter(Request.executor_id == executor_id)
        if department:
            query = query.join(Request.executor).filter(Employee.department == department)
        if overdue:
            query = query.filter(
                Request.deadline < datetime.utcnow(),
                Request.status != "done",
            )
        return query.order_by(Request.deadline).all()

    def overdue_in_progress_by_executor(self, executor_id: int) -> list[Request]:
        return (
            self.db.query(Request)
            .filter(
                Request.executor_id == executor_id,
                Request.status == "in_progress",
                Request.deadline < datetime.utcnow(),
            )
            .order_by(Request.deadline)
            .all()
        )

    def count_by_status(self) -> list[tuple[str, int]]:
        return (
            self.db.query(Request.status, func.count(Request.id))
            .group_by(Request.status)
            .all()
        )

    def count_overdue(self) -> int:
        return (
            self.db.query(func.count(Request.id))
            .filter(
                Request.deadline < datetime.utcnow(),
                Request.status != "done",
            )
            .scalar()
        )

    def completed_by_executor(self) -> list[tuple[str, int]]:
        return (
            self.db.query(
                Employee.full_name,
                func.count(Request.id).label("done_count"),
            )
            .join(Request, Request.executor_id == Employee.id)
            .filter(Request.status == "done")
            .group_by(Employee.id, Employee.full_name)
            .order_by(func.count(Request.id).desc())
            .all()
        )
