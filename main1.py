from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from routers.votes import router as votes_router
import os
import shutil
import schemas
import models
from models import User
from database import Base, engine, get_db
from auth import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
)
from validators import validate_upload_file
from seed import seed_admin
from admin import router as admin_router
from routers.admin_problems import admin_problems_router
from routers.notifications import router as notifications_router
from routers.trending import router as trending_router
from routers.profile import router as profile_router
from routers.bookmarks import router as bookmarks_router
from routers.admin_stats import router as admin_stats_router
from routers.saved import router as saved_router
from routers.comments import router as comments_router
from routers.saved_problems import router as saved_problems_router





# ---------------------------
# APP INIT
# ---------------------------
app = FastAPI(
    title="Split Repair Map",
    version="0.1.0",
    description="API za prijavu komunalnih problema u Splitu",
)

# ---------------------------
# DATABASE INIT
# ---------------------------
Base.metadata.create_all(bind=engine)


def seed_statuses():
    db = Session(bind=engine)
    for name in ["open", "pending", "resolved"]:
        if not db.query(models.Status).filter_by(name=name).first():
            db.add(models.Status(name=name))
    db.commit()
    db.close()


seed_admin()
seed_statuses()

# ---------------------------
# UPLOADS
# ---------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# ---------------------------
# EXCEPTION HANDLERS
# ---------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )


@app.exception_handler(IntegrityError)
async def db_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Database error"},
    )

# ---------------------------
# HEALTH
# ---------------------------
@app.get("/health")
def health_check():
    return {"status": "OK"}

# ---------------------------
# AUTH
# ---------------------------
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(username=user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = models.User(
        username=user.username,
        password=hash_password(user.password),
        is_admin=False,
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created"}


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter_by(username=form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ---------------------------
# PROBLEMS
# ---------------------------
@app.post("/problems", response_model=schemas.ProblemResponse)
async def create_problem(
    form: schemas.ProblemCreate = Depends(schemas.ProblemCreateForm),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_upload_file(file)

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        location = models.Location(
            latitude=form.latitude,
            longitude=form.longitude,
            address=form.address,
        )
        db.add(location)
        db.flush()

        status = db.query(models.Status).filter_by(name="open").first()

        problem = models.Problem(
            title=form.title,
            description=form.description,
            image_path=file_path,
            location_id=location.id,
            status_id=status.id,
            user_id=current_user.id,
        )

        db.add(problem)
        db.commit()
        db.refresh(problem)
        return problem

    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Greška pri spremanju problema")

@app.post("/problems/{problem_id}/comments", response_model=schemas.CommentOut)
def add_comment(
    problem_id: int,
    data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    comment = models.Comment(
        text=data.text,
        user_id=current_user.id,
        problem_id=problem_id
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    note = Notification(
    user_id=problem.user_id,
    message=f"Novi komentar na tvoj problem: {problem.title}"
    )

    db.add(note)
    db.commit()


    return {
        "id": comment.id,
        "text": comment.text,
        "created_at": comment.created_at,
        "username": current_user.username
    }

app.include_router(notifications_router)


@app.get("/problems/{problem_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(problem_id: int, db: Session = Depends(get_db)):
    return [
        {
            "id": c.id,
            "text": c.text,
            "created_at": c.created_at,
            "username": c.user.username
        }
        for c in db.query(models.Comment)
        .filter(models.Comment.problem_id == problem_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    ]

app.include_router(votes_router)

@app.get("/problems", response_model=dict)
def list_problems(
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(models.Problem)

    # FILTER PO STATUSU
    if status:
        status_obj = db.query(models.Status).filter(models.Status.name == status).first()
        if status_obj:
            query = query.filter(models.Problem.status_id == status_obj.id)

    # SEARCH PO NASLOVU I OPISU
    if search:
        query = query.filter(
            or_(
                models.Problem.title.ilike(f"%{search}%"),
                models.Problem.description.ilike(f"%{search}%")
            )
        )

    total = query.count()

    problems = (
        query
        .order_by(models.Problem.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": problems
    }


@app.get("/problems/{problem_id}", response_model=schemas.ProblemResponse)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter_by(id=problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

# ---------------------------
# CURRENT USER
# ---------------------------
@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
    }

# ---------------------------
# ROUTERS
# ---------------------------
app.include_router(admin_router)
app.include_router(admin_problems_router)

# ---------------------------
# OPENAPI (bez global auth)
# ---------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title="Split Repair Map",
        version="0.1.0",
        description="API za prijavu komunalnih problema u Splitu",
        routes=app.routes,
    )
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
app.include_router(trending_router)
app.include_router(profile_router)
app.include_router(bookmarks_router)
app.include_router(admin_stats_router)
app.include_router(saved_router)
app.include_router(comments_router)
app.include_router(saved_problems_router)
