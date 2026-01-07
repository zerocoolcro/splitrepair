from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User
from database import get_db
from auth import get_current_user, hash_password
from schemas import UserCreate

router = APIRouter(prefix="/admin", tags=["Admin"])

def admin_required(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user

@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    return db.query(User).all()

@router.post("/create_user")
def create_user_admin(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=user.username, password=hash_password(user.password), is_admin=0)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
