from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Problem, ProblemVote, User
from auth import get_current_user
from schemas import VoteOut

router = APIRouter(prefix="/problems", tags=["Votes"])

@router.post("/{problem_id}/vote", response_model=VoteOut)
def vote_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    existing = (
        db.query(ProblemVote)
        .filter(
            ProblemVote.user_id == current_user.id,
            ProblemVote.problem_id == problem_id
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Already voted")

    vote = ProblemVote(user_id=current_user.id, problem_id=problem_id)
    db.add(vote)
    db.commit()

    total = db.query(ProblemVote).filter(ProblemVote.problem_id == problem_id).count()

    return {"problem_id": problem_id, "votes": total}
