from sqlalchemy.orm import Session

from . import models, schemas


def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(title=project.title, author=project.author, project_type=project.project_type, file_path = project.file_path, img_file_path = project.img_file_path)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project