from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    project_type = Column(String, index=True)
    summary = Column(String, index=True)
    file_path = Column(String(255), index=True)



def __repr__(self):
        return '<Project %r>' % (self.id)