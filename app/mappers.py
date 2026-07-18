from app.domain.entities import EmployeeEntity, RequestEntity
from app.domain.enums import RequestStatus
from app.models import Employee, Request


def employee_to_entity(model: Employee) -> EmployeeEntity:
    return EmployeeEntity(
        id=model.id,
        full_name=model.full_name,
        department=model.department,
        position=model.position,
    )


def request_to_entity(model: Request, include_relations: bool = False) -> RequestEntity:
    entity = RequestEntity(
        id=model.id,
        number=model.number,
        created_at=model.created_at,
        author_id=model.author_id,
        executor_id=model.executor_id,
        description=model.description,
        deadline=model.deadline,
        status=RequestStatus(model.status),
    )
    if include_relations:
        if model.author:
            entity.author = employee_to_entity(model.author)
        if model.executor:
            entity.executor = employee_to_entity(model.executor)
    return entity
