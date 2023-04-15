from typing import List, Union

from pydantic import BaseModel

class ProjectBase(BaseModel):
    title: str
    author: str
    project_type: str
    summary: str
    file_path: str
    img_file_path: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    title: str
    author: str
    project_type: str
    summary: str
    file_path: str
    img_file_path: str

    class Config:
        orm_mode = True