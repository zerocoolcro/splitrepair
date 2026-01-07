from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
import shutil
import os
from datetime import datetime, timedelta
import schemas
from database import Base, engine, get_db
import models
from auth import get_current_user, hash_password, verify_password, SECRET_KEY, ALGORITHM, create_access_token
from jose import jwt
from fastapi.security import OAuth2PasswordRequestForm
from admin import router as admin_router
from routers.admin_problems import admin_problems_router
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from validators import validate_upload_file
from seed import seed_admin


# ---------------------------
# APP INIT
# ---------------------------
app = FastAPI(
    title="Split Repair Map",
    version="0.1.0",
    description="API za prijavu komunalnih problema u Splitu"
)

app.include_router(admin_problems_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()}
    )

@app.exception_handler(IntegrityError)
async def db_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Database error"}
    )

# ---------------------------
# DATABASE INIT
# ---------------------------
Base.metadata.create_all(bind=engine)
seed_admin()

def seed_statuses():
    db = Session(bind=engine)
    for name in ["open", "pending", "resolved"]:
        if not db.query(models.Status).filter_by(name=name).first():
            db.add(models.Status(name=name))
    db.commit()
    db.close()

seed_statuses()

# ---------------------------
# UPLOADS FOLDER
# ---------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")


# ---------------------------
# HEALTH CHECK
# ---------------------------
@app.get("/health")
def health_check():
    return {"status": "OK"}

# ---------------------------
# REGISTER
# ---------------------------
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hash_password(user.password)
    new_user = models.User(username=user.username, password=hashed, is_admin=0)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created"}

# ---------------------------
# LOGIN
# ---------------------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ---------------------------
# PROBLEMS CRUD
# ---------------------------
@app.post("/problems", response_model=schemas.ProblemResponse)
async def create_problem(
    form: schemas.ProblemCreate = Depends(schemas.ProblemCreateForm),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    validate_upload_file(file)

    try:
        # ensure uploads folder exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # SAVE FILE
        file_location = f"{UPLOAD_FOLDER}/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # CREATE LOCATION
        location = models.Location(
            latitude=form.latitude,
            longitude=form.longitude,
            address=form.address
        )
        db.add(location)
        db.flush()  # dobije location.id

        # GET OR CREATE STATUS
        status = db.query(models.Status).filter(models.Status.name == "open").first()
        if not status:
            status = models.Status(name="open")
            db.add(status)
            db.flush()

        # CREATE PROBLEM
        problem = models.Problem(
            title=form.title,
            description=form.description,
            image_path=file_location,
            location_id=location.id,
            status_id=status.id,
            user_id=current_user.id
        )

        db.add(problem)
        db.commit()
        db.refresh(problem)

        return problem

    except Exception as e:
        db.rollback()

        if os.path.exists(file_location):
            os.remove(file_location)

        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="Greška pri spremanju problema")




@app.get("/problems", response_model=list[schemas.ProblemResponse])
def list_problems(status: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Problem)
    if status:
        status_obj = db.query(models.Status).filter(models.Status.name == status).first()
        if status_obj:
            query = query.filter(models.Problem.status_id == status_obj.id)
    return query.order_by(models.Problem.created_at.desc()).all()

@app.get("/problems/{problem_id}", response_model=schemas.ProblemResponse)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem
    
    
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# --------------------------
# OVO JE DA VIDIM RADI LI TOKEN
# --------------------------
@app.get("/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }


# ---------------------------
# CUSTOM OPENAPI
# ---------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Split Repair Map",
        version="0.1.0",
        description="API za prijavu komunalnih problema u Splitu",
        routes=app.routes,
    )

    # ⚠️ NEMA global security!
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# ---------------------------
# INCLUDE ADMIN ROUTER
# ---------------------------
app.include_router(admin_router)