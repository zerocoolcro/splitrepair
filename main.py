from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Security, APIRouter
from database import Base, engine, SessionLocal, get_db
import schemas
from models import User
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import shutil
import os
from fastapi.openapi.utils import get_openapi
from auth import get_current_user

app = FastAPI(
    title="Split Repair Map",
    version="0.1.0",
    description="API za prijavu komunalnih problema u Splitu"
)

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


Base.metadata.create_all(bind=engine)

def create_initial_admin():
    """
    Kreira admin korisnika ako ga nema. Podatke uzima iz env varijabli:
    ADMIN_USERNAME i ADMIN_PASSWORD.
    Ako nisu postavljene, funkcija neće kreirati administratorski račun
    (smanjuje rizik hard-coded lozinki).
    """
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_username or not admin_password:
        # Ne stvaraj fallback admina bez eksplicitnih varijabli
        return

    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.username == admin_username).first()
        if existing:
            # ako već postoji, osiguraj da je admin (možeš odlučiti hoće li postaviti flag)
            if existing.is_admin != 1:
                existing.is_admin = 1
                db.commit()
            return

        # stvori admin korisnika
        hashed = hash_password(admin_password)
        admin = models.User(username=admin_username, password=hashed, is_admin=1)
        db.add(admin)
        db.commit()
    finally:
        db.close()

# Pozovi funkciju pri startupu aplikacije
@app.on_event("startup")
def on_startup():
    create_initial_admin()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


def admin_required(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user


# 1) GET /admin/users – lista svih korisnika
@admin_router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    return db.query(User).all()


# 2) POST /admin/create_user – stvara korisnika (može biti admin)
from schemas import UserCreate
from auth import hash_password

@admin_router.post("/create_user")
def create_user_admin(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user.username,
        password=hash_password(user.password),
        is_admin=user.is_admin  # ovo omogućuje stvaranje admina
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# 3) DELETE /admin/users/{id} – admin može brisati bilo koga
@admin_router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# --------------------------
# CUSTOM SWAGGER AUTH (VALUE POLJE)
# --------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Split Repair Map",
        version="0.1.0",
        description="API za prijavu komunalnih problema u Splitu",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # automatski dodaj security na sve endpointe koji koriste get_current_user
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi



@app.get("/health")
def health_check():
    return {"status": "OK"}


@app.post("/problems", response_model=schemas.ProblemResponse)
async def create_problem(
    title: str = Form(...),
    description: str = Form(...),
    latitude: str = Form(None),
    longitude: str = Form(None),
    address: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda: get_current_user())
):
    user_id = current_user.id

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    file_location = f"{upload_folder}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    location = models.Location(
        latitude=latitude,
        longitude=longitude,
        address=address
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    status = db.query(models.Status).filter(models.Status.name == "open").first()
    if not status:
        status = models.Status(name="open")
        db.add(status)
        db.commit()
        db.refresh(status)

    problem = models.Problem(
        title=title,
        description=description,
        image_path=file_location,
        location_id=location.id,
        status_id=status.id,
        user_id=user_id
    )

    db.add(problem)
    db.commit()
    db.refresh(problem)

    return problem



@app.get("/problems", response_model=list[schemas.ProblemResponse])
def list_problems(status: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Problem)

    if status:
        status_obj = db.query(models.Status).filter(models.Status.name == status).first()
        if status_obj:
            query = query.filter(models.Problem.status_id == status_obj.id)

    problems = query.order_by(models.Problem.created_at.desc()).all()
    return problems


@app.get("/problems/{problem_id}", response_model=schemas.ProblemResponse)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem



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


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})

    return {"access_token": token, "token_type": "bearer"}

app.include_router(admin_router)
