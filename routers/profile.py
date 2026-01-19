from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, Problem, ProblemVote
from auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problems = (
        db.query(
            Problem,
            func.count(ProblemVote.id).label("votes")
        )
        .outerjoin(ProblemVote)
        .filter(Problem.user_id == current_user.id)
        .group_by(Problem.id)
        .all()
    )

    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "problems": [
            {
                "id": p.id,
                "title": p.title,
                "votes": votes,
                "status": p.status.name,
                "created_at": p.created_at
            }
            for p, votes in problems
        ]
    }
