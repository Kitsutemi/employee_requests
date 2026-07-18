from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.enums import RequestStatus
from app.mappers import request_to_entity
from app.models import Request
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.request_repository import RequestRepository


class RequestService:
    def __init__(self, db: Session):
        self.repo = RequestRepository(db)
        self.employee_repo = EmployeeRepository(db)

    def generate_number(self) -> str:
        last = self.repo.get_last()
        next_num = (last.id + 1) if last else 1
        return f"REQ-{datetime.utcnow().year}-{next_num:06d}"

    def create(
        self,
        author_id: int,
        executor_id: int,
        description: str,
        deadline: datetime,
    ) -> Request:
        if not self.employee_repo.get_by_id(author_id):
            raise ValueError("Автор не найден")
        if not self.employee_repo.get_by_id(executor_id):
            raise ValueError("Исполнитель не найден")

        request = Request(
            number=self.generate_number(),
            author_id=author_id,
            executor_id=executor_id,
            description=description,
            deadline=deadline,
            status=RequestStatus.NEW.value,
        )
        return self.repo.create(request)

    def update_status(self, request_id: int, new_status: str) -> Request:
        request = self.repo.get_by_id(request_id)
        if not request:
            raise LookupError("Заявка не найдена")

        entity = request_to_entity(request)
        entity.transition_to(RequestStatus(new_status))
        request.status = entity.status.value
        return self.repo.save(request)

    def update_executor(self, request_id: int, executor_id: int) -> Request:
        request = self.repo.get_by_id(request_id)
        if not request:
            raise LookupError("Заявка не найдена")
        if not self.employee_repo.get_by_id(executor_id):
            raise ValueError("Исполнитель не найден")

        entity = request_to_entity(request)
        entity.change_executor(executor_id)
        request.executor_id = entity.executor_id
        return self.repo.save(request)
