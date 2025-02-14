import io
import sys
import fitz
import shutil
from typing import List, Optional
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pypdfium2 as pdfium
import sqlite3
from PIL import Image



from fastapi import FastAPI, Form, status, Request, Depends, HTTPException, File, UploadFile, Response
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


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


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

#Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

templates = Jinja2Templates(directory="templates")
env = Environment(loader=FileSystemLoader('templates'))

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/pdfjs", StaticFiles(directory="pdfjs"), name="pdfjs")

def get_pdf_data(id):
    conn = sqlite3.connect("app.db")
    cursor= conn.cursor()

    cursor.execute("SELECT file_path FROM project WHERE id=?", (id,))
    pdf_data = cursor.fetchone()[0]

    conn.close()

    return pdf_data


@app.get("/pdf/{project_id}")
async def pdf(request: Request, project_id: int):

    pdf_data = get_pdf_data(project_id)

    tmeplate = env.get_template('pdf-view-page.html')
    context = {'pdf_data': pdf_data}
    html_content=tmeplate.render(context)

    return templates.TemplateResponse("pdf-view-page.html", {"request": request, "pdf_data": pdf_data})

@app.get("/search/")
def search(request: Request, query: Optional[str], db: Session = Depends(get_db)):
    projs = db.query(models.Project).filter(models.Project.title.contains(query)).all()
    return templates.TemplateResponse(
        "browse-page.html", {"request": request, "projs": projs}
    )

@app.get("/dr.hill/")
def drhill(request: Request, db:Session= Depends(get_db)):
    filter = "Dr. Stephen Hill"
    projs = db.query(models.Project).filter(models.Project.project_manager.contains(filter)).all()
    return templates.TemplateResponse("browse-page.html", {"request": request, "projs": projs})

@app.get("/erin_lake/")
def elakeS(request: Request, db:Session= Depends(get_db)):
    filter = "Erin Lake"
    projs = db.query(models.Project).filter(models.Project.project_manager.contains(filter)).all()
    return templates.TemplateResponse("browse-page.html", {"request": request, "projs": projs})

@app.get("/")
async def Home(request: Request):
    return templates.TemplateResponse("home-page.html", {"request": request})

@app.get("/indexHome")
async def Home(request: Request):
    return templates.TemplateResponse("indexHome.html", {"request": request})

@app.get("/browse-page")
async def browse_page(request: Request, db:Session = Depends(get_db)):
    project = db.query(models.Project).all()
    return templates.TemplateResponse("browse-page.html", {"request": request, "projs": project})
    
@app.get("/projects_all")
def read_projects(db:Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return projects


@app.get("/index")
async def home(request: Request, db: Session = Depends(get_db)):
    project = db.query(models.Project).all()
    return templates.TemplateResponse("index.html", {"request": request, "project": project})
 
@app.post("/add_project")
async def add(request: Request, title: str = Form(...), author: str = Form(...), project_type: str = Form(...),summary: str = Form(...), project_manager: str = Form(...), semester: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    path = f"./uploads/{file.filename.split('.')[0]}"
    os.mkdir(path=path)

    with open(f"./uploads/{file.filename.split('.')[0]}/{file.filename}","wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    filepath=  f"./uploads/{file.filename.split('.')[0]}/{file.filename}"
    pdffil= pdfium.PdfDocument(filepath)

    page = pdffil[0]
    pil_image = page.render(scale=2).to_pil()
    pil_image.save(f"./uploads/{file.filename.split('.')[0]}/{file.filename.split('.')[0]}_img.jpg")
    new_file = models.Project(title=title, author=author, project_type=project_type, summary = summary, project_manager=project_manager, semester= semester, file_path=f"{file.filename.split('.')[0]}/{file.filename}", img_file_path = f"{file.filename.split('.')[0]}/{file.filename.split('.')[0]}_img.jpg")
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return RedirectResponse(url=app.url_path_for("Home"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/upload-page")
async def upload_page(request: Request):
    return templates.TemplateResponse("upload-page.html", {"request": request})

@app.get("/uploads/{project_img_name}")
async def imgsrc(request: Request, project_img_name: str, db: Session = Depends(get_db)):
    project_img = db.query(models.Project).filter(models.Project.img_file_path == project_img_name).first
    return project_img

@app.get("/delete/{project_id}")
async def delete(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id)
    db.delete(project)
    db.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)