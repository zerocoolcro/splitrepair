from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Problem, ProblemVote

router = APIRouter(prefix="/trending", tags=["Trending"])

@router.get("/")
def get_trending_problems(db: Session = Depends(get_db)):
    results = (
        db.query(
            Problem,
            func.count(ProblemVote.id).label("votes")
        )
        .outerjoin(ProblemVote)
        .group_by(Problem.id)
        .order_by(func.count(ProblemVote.id).desc())
        .limit(5)
        .all()
    )

    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "votes": votes,
            "created_at": p.created_at
        }
        for p, votes in results
    ]
