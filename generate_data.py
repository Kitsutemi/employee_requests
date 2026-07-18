import random
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import Employee, Request
from tqdm import tqdm
import time


def generate_employees(n=1000):
    db = SessionLocal()
    departments = ["IT", "HR", "Finance", "Marketing", "Sales", "R&D", "Logistics", "Legal", "Operations"]
    positions = ["Junior", "Middle", "Senior", "Lead", "Manager", "Director", "Assistant", "Analyst"]
    employees = []
    for i in range(n):
        emp = Employee(
            full_name=f"Employee {i}",
            department=random.choice(departments),
            position=random.choice(positions)
        )
        employees.append(emp)
    db.add_all(employees)
    db.commit()
    db.close()


def generate_requests(n=1_000_000):
    db = SessionLocal()
    employee_ids = [e.id for e in db.query(Employee.id).all()]
    if not employee_ids:
        raise Exception("Сначала создайте сотрудников!")
    statuses = ["new", "in_progress", "done"]
    batch_size = 10000
    start_time = time.time()

    for i in tqdm(range(0, n, batch_size), desc="Генерация заявок"):
        requests = []
        for j in range(batch_size):
            created = datetime.now() - timedelta(days=random.randint(0, 365))
            deadline = created + timedelta(days=random.randint(1, 30))
            status = random.choices(statuses, weights=[0.2, 0.3, 0.5])[0]
            req = Request(
                number=f"REQ-{datetime.now().year}-{i+j+1:06d}",
                created_at=created,
                author_id=random.choice(employee_ids),
                executor_id=random.choice(employee_ids),
                description=f"Описание заявки {i+j+1}",
                deadline=deadline,
                status=status
            )
            requests.append(req)
        db.add_all(requests)
        db.commit()
    db.close()
    print(f"Генерация {n} заявок заняла {time.time() - start_time:.2f} с")


if __name__ == "__main__":
    # Пересоздаём таблицы (чистый старт)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Создание сотрудников...")
    generate_employees(1000)
    print("Создание заявок (1 000 000)...")
    generate_requests(1_000_000)
    print("Готово!")