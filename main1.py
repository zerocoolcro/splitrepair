from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

import os
import shutil

import models
import schemas
from database import Base, engine, get_db
from auth import get_current_user, hash_password, verify_password, create_access_token
from validators import validate_upload_file
from seed import seed_admin
from fastapi import WebSocket, WebSocketDisconnect
from websocket_manager import manager
from dependencies import get_current_user_ws


# Routers
from routers.votes import router as votes_router
from routers.notifications import router as notifications_router
from routers.trending import router as trending_router
from routers.profile import router as profile_router
from routers.bookmarks import router as bookmarks_router
from routers.admin_stats import router as admin_stats_router
from routers.saved import router as saved_router
from routers.comments import router as comments_router
from routers.saved_problems import router as saved_problems_router
from admin import router as admin_router
from routers.admin_problems import admin_problems_router

# ---------------------------
# APP INIT
# ---------------------------
app = FastAPI(
    title="Split Repair Map",
    version="0.1.0",
    description="API za prijavu komunalnih problema u Splitu",
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ---------------------------
# DATABASE INIT
# ---------------------------
Base.metadata.create_all(bind=engine)

# Seed admin user and statuses
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
# CORS CONFIG
# ---------------------------
origins = ["http://localhost:5173",
           "http://127.0.0.1:5173",
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# HEALTH CHECK
# ---------------------------
@app.get("/health")
def health_check():
    return {"status": "OK"}


# ---------------------------
# WEB SOCKET
# ---------------------------
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    user = await get_current_user_ws(websocket)
    await manager.connect(user.id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)


# ---------------------------
# AUTH
# ---------------------------
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

    print("USER DATA:", user.model_dump())  # 👈 VAŽNO (ne dict())

    if db.query(models.User).filter_by(username=user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(models.User).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
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
# CREATE PROBLEM
# ---------------------------
@app.post("/problems", response_model=schemas.ProblemResponse)
async def create_problem(
    form: schemas.ProblemCreate = Depends(schemas.ProblemCreateForm),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    validate_upload_file(file)
    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create location
        location = models.Location(
            latitude=form.latitude,
            longitude=form.longitude,
            address=form.address,
        )
        db.add(location)
        db.flush()

        # Get default status
        status = db.query(models.Status).filter_by(name="open").first()

        # Create problem
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
        return schemas.ProblemResponse(
            id=problem.id,
            title=problem.title,
            description=problem.description,
            image_path=problem.image_path,
            image_url=f"/{problem.image_path}",
            created_at=problem.created_at,
            status=schemas.StatusOut(name=status.name),
            location=schemas.LocationOut(
                latitude=location.latitude,
                longitude=location.longitude,
                address=location.address
            ),
            user_id=current_user.id
        )

    except Exception:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Greška pri spremanju problema")

# ---------------------------
# LIST PROBLEMS
# ---------------------------
@app.get("/problems", response_model=schemas.ProblemListResponse)
def list_problems(
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    query = db.query(models.Problem).join(models.Status, isouter=True).join(models.Location, isouter=True)

    if status:
        query = query.filter(models.Status.name == status)

    if search:
        query = query.filter(
            or_(
                models.Problem.title.ilike(f"%{search}%"),
                models.Problem.description.ilike(f"%{search}%")
            )
        )

    total = query.count()
    problems = query.order_by(models.Problem.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for p in problems:
        location_out = None
        if p.location:
            location_out = schemas.LocationOut(
            latitude=p.location.latitude,
            longitude=p.location.longitude,
            address=p.location.address
        )

        status_out = schemas.StatusOut(
            name=p.status.name if p.status else "unknown"
        )

        items.append(
            schemas.ProblemResponse(
                id=p.id,
                title=p.title,
                description=p.description,
                image_path=p.image_path,
                image_url=f"/{p.image_path}" if p.image_path else None,
                created_at=p.created_at,
                status=status_out,
                location=location_out,
                user_id=p.user_id
            )
        )

    total_pages = (total + limit - 1) // limit  # zaokružuje gore
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return schemas.ProblemListResponse(
        page = page,
        limit = limit,
        total = total,
        total_pages = total_pages,
        next_page = next_page,
        prev_page = prev_page,
        items = items
    )

# ---------------------------
# GET SINGLE PROBLEM
# ---------------------------
@app.get("/problems/{problem_id}", response_model=schemas.ProblemResponse)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter_by(id=problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    location_out = None
    if problem.location:
        location_out = schemas.LocationOut(
            latitude=problem.location.latitude,
            longitude=problem.location.longitude,
            address=problem.location.address
        )

    status_out = schemas.StatusOut(name=problem.status.name if problem.status else "unknown")

    return schemas.ProblemResponse(
        id=problem.id,
        title=problem.title,
        description=problem.description,
        image_path=problem.image_path,
        image_url=f"/{problem.image_path}" if problem.image_path else None,
        created_at=problem.created_at,
        status=status_out,
        location=location_out,
        user_id=problem.user_id
    )

# ---------------------------
# COMMENTS
# ---------------------------
@app.post("/problems/{problem_id}/comments", response_model=schemas.CommentOut)
def add_comment(
    problem_id: int,
    data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
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

    # Notification
    if hasattr(models, "Notification"):
        note = models.Notification(
            user_id=problem.user_id,
            message=f"Novi komentar na tvoj problem: {problem.title}"
        )
        db.add(note)
        db.commit()

    return schemas.CommentOut(
        id=comment.id,
        text=comment.text,
        created_at=comment.created_at,
        username=current_user.username
    )

@app.get("/problems/{problem_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(problem_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.problem_id == problem_id).order_by(models.Comment.created_at.asc()).all()
    return [
        schemas.CommentOut(
            id=c.id,
            text=c.text,
            created_at=c.created_at,
            username=c.user.username
        )
        for c in comments
    ]

# ---------------------------
# CURRENT USER
# ---------------------------
@app.get("/me")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return schemas.UserOut(
        id=current_user.id,
        username=current_user.username,
        role="admin" if current_user.is_admin else "user"
    )

# ---------------------------
# INCLUDE ROUTERS
# ---------------------------
app.include_router(admin_router)
app.include_router(admin_problems_router)
app.include_router(votes_router)
app.include_router(notifications_router)
app.include_router(trending_router)
app.include_router(profile_router)
app.include_router(bookmarks_router)
app.include_router(admin_stats_router)
app.include_router(saved_router)
app.include_router(comments_router)
app.include_router(saved_problems_router)

# ---------------------------
# OPENAPI (custom)
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

