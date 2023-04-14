import io
import sys
import fitz
import shutil
from typing import List
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pypdfium2 as pdfium

from PIL import Image



from fastapi import FastAPI, Form, status, Request, Depends, HTTPException, File, UploadFile, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path


from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from .import crud, models, schemas
from .database import SessionLocal, engine

from .library.helpers import *
from app.routers import twoforms, unsplash, accordion

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
Base = declarative_base()


#Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(unsplash.router)
app.include_router(twoforms.router)
app.include_router(accordion.router)


@app.get("/pdf")
async def pdf():
    return FileResponse("uploads/BoakaiKMameyBlueBirdScan.pdf")

@app.get("/pdf-page")
async def pdfview(request: Request):
    return templates.TemplateResponse("pdf-view-page.html", {"request": request})

@app.get("/")
async def Home(request: Request):
    return templates.TemplateResponse("home-page.html", {"request": request})

@app.get("/browse-page")
async def browse_page(request: Request):
    return templates.TemplateResponse("browse-page.html", {"request": request})
    

@app.get("/index")
async def home(request: Request, db: Session = Depends(get_db)):
    project = db.query(models.Project).order_by(models.Project.id.desc())
    return templates.TemplateResponse("index.html", {"request": request, "project": project})
 
@app.post("/add_project")
async def add(request: Request, title: str = Form(...), author: str = Form(...), project_type: str = Form(...),summary: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):

    with open(f"C:/Users/kushi/Desktop/Online_Web_Interface/uploads/{file.filename}","wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    filepath=  f"C:/Users/kushi/Desktop/Online_Web_Interface/uploads/{file.filename}"
    pdffil= pdfium.PdfDocument(filepath)

    page = pdffil[0]
    pil_image = page.render(scale=2).to_pil()
    pil_image.save(f"C:/Users/kushi/Desktop/Online_Web_Interface/uploads/{file.filename}img.jpg")


    
    new_file = models.Project(title=title, author=author, project_type=project_type, summary = summary, file_path=f"C:/Users/kushi/Desktop/Online_Web_Interface/uploads/{file.filename}")
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return RedirectResponse(url=app.url_path_for("Home"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/upload-page")
async def upload_page(request: Request):
    return templates.TemplateResponse("upload-page.html", {"request": request})


@app.get("/delete/{project_id}")
async def delete(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    db.delete(project)
    db.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)

