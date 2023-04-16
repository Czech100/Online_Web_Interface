from sqlalchemy.orm import Session

from . import models, schemas


def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(title=project.title, author=project.author, project_type=project.project_type, file_path = project.file_path, img_file_path = project.img_file_path)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_file_path(db:Session, file_path:str):
    return db.query(models.Project).filter(models.Project.file_path == file_path).first

def search_proj(query:str, db:Session):
    projs = db.query(models.Project).filter(models.Project.title.contains(query))
    return projs