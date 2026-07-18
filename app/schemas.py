from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EmployeeBase(BaseModel):
    full_name: str
    department: str
    position: str


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: int
    model_config = {"from_attributes": True}


class RequestBase(BaseModel):
    author_id: int
    executor_id: int
    description: str
    deadline: datetime


class RequestCreate(RequestBase):
    pass


class RequestUpdateStatus(BaseModel):
    status: str


class RequestUpdateExecutor(BaseModel):
    executor_id: int


class Request(RequestBase):
    id: int
    number: str
    created_at: datetime
    status: str
    author: Optional[Employee] = None
    executor: Optional[Employee] = None

    model_config = {"from_attributes": True}