from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Problem, SavedProblem, User
from auth import get_current_user

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@router.post("/{problem_id}")
def save_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    exists = (
        db.query(SavedProblem)
        .filter(
            SavedProblem.user_id == current_user.id,
            SavedProblem.problem_id == problem_id
        )
        .first()
    )

    if exists:
        raise HTTPException(status_code=400, detail="Already saved")

    saved = SavedProblem(user_id=current_user.id, problem_id=problem_id)
    db.add(saved)
    db.commit()

    return {"message": "Problem saved"}

@router.delete("/{problem_id}")
def unsave_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved = (
        db.query(SavedProblem)
        .filter(
            SavedProblem.user_id == current_user.id,
            SavedProblem.problem_id == problem_id
        )
        .first()
    )

    if not saved:
        raise HTTPException(status_code=404, detail="Not saved")

    db.delete(saved)
    db.commit()

    return {"message": "Problem removed from bookmarks"}

@router.get("/")
def list_saved(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved = (
        db.query(SavedProblem)
        .filter(SavedProblem.user_id == current_user.id)
        .all()
    )

    return [
        {
            "id": s.problem.id,
            "title": s.problem.title,
            "status": s.problem.status.name,
            "created_at": s.problem.created_at
        }
        for s in saved
    ]
