from typing import List

from fastapi import FastAPI, Form, status, Request, Depends, HTTPException, File, UploadFile, Response
from fastapi.responses import HTMLResponse, StreamingResponse
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


@app.get("/pdf_viewer")
async def get_pdf():
    with open("uploads/BoakaiKMameyBlueBirdScan.pdf", "rb") as pdf_file:
        pdf = pdf_file.read()
    return Response(content=pdf, media_type="application/pdf")



@app.get("/")
async def root(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF.js Example</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.min.js"></script>
    </head>
    <body>
        <div>
            <canvas id="pdf-canvas"></canvas>
        </div>
        <script>
            pdfjsLib.getDocument("/pdf_viewer").promise.then(function(pdf) {
                pdf.getPage(1).then(function(page) {
                    var canvas = document.getElementById("pdf-canvas");
                    var context = canvas.getContext("2d");
                    var viewport = page.getViewport({scale: 1});
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    page.render({canvasContext: context, viewport: viewport});
                });
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
    

@app.get("/index")
async def home(request: Request, db: Session = Depends(get_db)):
    project = db.query(models.Project).order_by(models.Project.id.desc())
    return templates.TemplateResponse("index.html", {"request": request, "project": project})
 
@app.post("/add_project")
async def add(request: Request, title: str = Form(...), author: str = Form(...), project_type: str = Form(...),summary: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    with open(f"C:/Users/kushi/Desktop/fastapi-web-starter-main/uploads/{file.filename}","wb") as f:
        f.write(contents)

    new_file = models.Project(title=title, author=author, project_type=project_type, summary = summary, file_path=f"C:/Users/kushi/Desktop/fastapi-web-starter-main/uploads/{file.filename}")
    
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/addnew")
async def addnew(request: Request):
    return templates.TemplateResponse("addnew.html", {"request": request})


@app.get("/delete/{project_id}")
async def delete(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    db.delete(project)
    db.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/page/{page_name}", response_class=HTMLResponse)
async def show_page(request: Request, page_name: str):
    data = openfile(page_name+".md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})
