from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, Problem, Comment, ProblemVote, SavedProblem
from auth import get_current_user

router = APIRouter(prefix="/admin/stats", tags=["Admin - Stats"])

def admin_required(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user

@router.get("/")
def get_stats(
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    return {
        "users": db.query(User).count(),
        "problems": db.query(Problem).count(),
        "comments": db.query(Comment).count(),
        "votes": db.query(ProblemVote).count(),
        "saved": db.query(SavedProblem).count()
    }
