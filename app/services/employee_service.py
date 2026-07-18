from sqlalchemy.orm import Session

from app.repositories.employee_repository import EmployeeRepository


class EmployeeService:
    def __init__(self, db: Session):
        self.repo = EmployeeRepository(db)

    def list_all(self):
        return self.repo.get_all()

    def create(self, full_name: str, department: str, position: str):
        return self.repo.create(full_name, department, position)

    def delete(self, employee_id: int) -> bool:
        return self.repo.delete(employee_id)

    def list_departments(self) -> list[str]:
        return self.repo.get_departments()
