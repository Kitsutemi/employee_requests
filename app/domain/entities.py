from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.enums import RequestStatus
from app.domain.rules import StatusTransitionRules


@dataclass
class EmployeeEntity:
    id: Optional[int]
    full_name: str
    department: str
    position: str


@dataclass
class RequestEntity:
    id: Optional[int]
    number: str
    created_at: datetime
    author_id: int
    executor_id: int
    description: str
    deadline: datetime
    status: RequestStatus
    author: Optional[EmployeeEntity] = None
    executor: Optional[EmployeeEntity] = None

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return self.status != RequestStatus.DONE and self.deadline < now

    def can_transition_to(self, new_status: RequestStatus) -> bool:
        return StatusTransitionRules.is_allowed(self.status, new_status)

    def transition_to(self, new_status: RequestStatus) -> None:
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Недопустимый переход из «{self.status.label}» в «{new_status.label}»"
            )
        self.status = new_status

    def can_change_executor(self) -> bool:
        return self.status != RequestStatus.DONE

    def change_executor(self, executor_id: int) -> None:
        if not self.can_change_executor():
            raise ValueError("Нельзя менять исполнителя у выполненной заявки")
        self.executor_id = executor_id
