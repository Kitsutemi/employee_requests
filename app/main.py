from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os

from app.database import SessionLocal, engine
from app import models, schemas
from app.domain.enums import RequestStatus
from app.services.employee_service import EmployeeService
from app.services.report_service import ReportService
from app.services.request_service import RequestService

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Учёт заявок сотрудников")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(PROJECT_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_DIR, "static")), name="static")

STATUS_LABELS = {
    RequestStatus.NEW.value: "Новая",
    RequestStatus.IN_PROGRESS.value: "В работе",
    RequestStatus.DONE.value: "Выполнена",
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _optional_str(value: Optional[str]) -> Optional[str]:
    if value is None or value.strip() == "":
        return None
    return value


def _optional_int(value: Optional[str]) -> Optional[int]:
    cleaned = _optional_str(value)
    if cleaned is None:
        return None
    return int(cleaned)


def _optional_bool(value: Optional[str]) -> bool:
    return value in ("true", "1", "on", "yes")


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    status: Optional[str] = Query(None),
    executor_id: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    overdue: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    from app.repositories.request_repository import RequestRepository

    repo = RequestRepository(db)
    employee_service = EmployeeService(db)

    status_filter = _optional_str(status)
    executor_filter = _optional_int(executor_id)
    department_filter = _optional_str(department)
    overdue_filter = _optional_bool(overdue)

    requests, total = repo.list_filtered(
        status=status_filter,
        executor_id=executor_filter,
        department=department_filter,
        overdue=overdue_filter,
        page=page,
        page_size=50,
    )
    executors = employee_service.list_all()
    departments = employee_service.list_departments()
    total_pages = max(1, (total + 49) // 50)

    return templates.TemplateResponse(
        request,
        "requests.html",
        {
            "requests": requests,
            "executors": executors,
            "departments": departments,
            "selected_status": status_filter,
            "selected_executor": executor_filter,
            "selected_department": department_filter,
            "overdue": overdue_filter,
            "page": page,
            "total_pages": total_pages,
            "total_count": total,
            "status_labels": STATUS_LABELS,
            "now": datetime.utcnow().strftime("%Y-%m-%d"),
            "active_page": "requests",
        },
    )


@app.get("/employees", response_class=HTMLResponse)
async def employees_page(request: Request, db: Session = Depends(get_db)):
    employees = EmployeeService(db).list_all()
    return templates.TemplateResponse(
        request, "employees.html", {"employees": employees, "active_page": "employees"}
    )


@app.post("/employees/add")
async def add_employee(
    full_name: str = Form(...),
    department: str = Form(...),
    position: str = Form(...),
    db: Session = Depends(get_db),
):
    EmployeeService(db).create(full_name, department, position)
    return RedirectResponse(url="/employees", status_code=303)


@app.get("/employees/{emp_id}/delete")
async def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    EmployeeService(db).delete(emp_id)
    return RedirectResponse(url="/employees", status_code=303)


@app.get("/requests/new", response_class=HTMLResponse)
async def new_request_form(request: Request, db: Session = Depends(get_db)):
    employees = EmployeeService(db).list_all()
    return templates.TemplateResponse(
        request,
        "request_form.html",
        {"employees": employees, "edit": False, "active_page": "new_request"},
    )


@app.post("/requests/create")
async def create_request(
    author_id: int = Form(...),
    executor_id: int = Form(...),
    description: str = Form(...),
    deadline: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        deadline_dt = datetime.fromisoformat(deadline)
    except ValueError as exc:
        raise HTTPException(400, "Неверный формат даты") from exc

    try:
        RequestService(db).create(author_id, executor_id, description, deadline_dt)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return RedirectResponse(url="/", status_code=303)


@app.post("/requests/{req_id}/update_status")
async def update_status_post(
    req_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        RequestService(db).update_status(req_id, status)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return RedirectResponse(url="/", status_code=303)


@app.post("/requests/{req_id}/update_executor")
async def update_executor(
    req_id: int,
    executor_id: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        RequestService(db).update_executor(req_id, executor_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return RedirectResponse(url="/", status_code=303)


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Session = Depends(get_db)):
    report_service = ReportService(db)
    status_counts = [
        (STATUS_LABELS.get(status, status), count)
        for status, count in report_service.status_summary()
    ]

    return templates.TemplateResponse(
        request,
        "reports.html",
        {
            "status_counts": status_counts,
            "overdue_count": report_service.overdue_count(),
            "done_by_executor": report_service.completed_by_executor(),
            "active_page": "reports",
        },
    )


@app.post("/api/requests/", response_model=schemas.Request)
def create_request_api(req: schemas.RequestCreate, db: Session = Depends(get_db)):
    try:
        db_req = RequestService(db).create(
            req.author_id, req.executor_id, req.description, req.deadline
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return db_req


@app.put("/api/requests/{req_id}/status")
def update_status_api(
    req_id: int, status_data: schemas.RequestUpdateStatus, db: Session = Depends(get_db)
):
    try:
        RequestService(db).update_status(req_id, status_data.status)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"message": f"Статус изменён на {status_data.status}"}


@app.put("/api/requests/{req_id}/executor")
def update_executor_api(
    req_id: int, exec_data: schemas.RequestUpdateExecutor, db: Session = Depends(get_db)
):
    try:
        RequestService(db).update_executor(req_id, exec_data.executor_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"message": "Исполнитель изменён"}


@app.get("/api/requests/")
def list_requests_api(
    status: Optional[str] = None,
    executor_id: Optional[str] = None,
    department: Optional[str] = None,
    overdue: Optional[str] = None,
    db: Session = Depends(get_db),
):
    from app.repositories.request_repository import RequestRepository

    return RequestRepository(db).list_api(
        status=_optional_str(status),
        executor_id=_optional_int(executor_id),
        department=_optional_str(department),
        overdue=_optional_bool(overdue),
    )
