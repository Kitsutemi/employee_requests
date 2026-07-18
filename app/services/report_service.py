from sqlalchemy.orm import Session

from app.repositories.request_repository import RequestRepository


class ReportService:
    def __init__(self, db: Session):
        self.repo = RequestRepository(db)

    def status_summary(self):
        return self.repo.count_by_status()

    def overdue_count(self) -> int:
        return self.repo.count_overdue()

    def completed_by_executor(self):
        return self.repo.completed_by_executor()
