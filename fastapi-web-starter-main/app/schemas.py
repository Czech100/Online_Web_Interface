from typing import List, Union

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: Union[str, None] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    title: str
    author: str
    project_type: str
    summary: str
    file_path: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    title: str
    author: str
    project_type: str
    summary: str
    file_path: str

    class Config:
        orm_mode = True
