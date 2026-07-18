from typing import Optional

from sqlalchemy.orm import Session

from app.models import Employee


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Employee]:
        return self.db.query(Employee).order_by(Employee.full_name).all()

    def get_by_id(self, employee_id: int) -> Optional[Employee]:
        return self.db.query(Employee).filter(Employee.id == employee_id).first()

    def create(self, full_name: str, department: str, position: str) -> Employee:
        employee = Employee(
            full_name=full_name,
            department=department,
            position=position,
        )
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete(self, employee_id: int) -> bool:
        employee = self.get_by_id(employee_id)
        if not employee:
            return False
        self.db.delete(employee)
        self.db.commit()
        return True

    def get_departments(self) -> list[str]:
        rows = (
            self.db.query(Employee.department)
            .distinct()
            .order_by(Employee.department)
            .all()
        )
        return [row[0] for row in rows]
