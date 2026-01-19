from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SavedProblem, Problem, User
from auth import get_current_user

router = APIRouter(prefix="/saved", tags=["Saved Problems"])

# Spremi problem
@router.post("/{problem_id}")
def save_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(SavedProblem).filter(
        SavedProblem.user_id == current_user.id,
        SavedProblem.problem_id == problem_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Problem already saved")

    saved = SavedProblem(user_id=current_user.id, problem_id=problem_id)
    db.add(saved)
    db.commit()
    return {"message": "Problem saved"}

# Ukloni problem iz spremljenih
@router.delete("/{problem_id}")
def remove_saved_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved = db.query(SavedProblem).filter(
        SavedProblem.user_id == current_user.id,
        SavedProblem.problem_id == problem_id
    ).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Problem not found in saved list")

    db.delete(saved)
    db.commit()
    return {"message": "Problem removed from saved list"}

# Lista svih spremljenih problema
@router.get("/", response_model=list[dict])
def list_saved_problems(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved = db.query(SavedProblem).filter(SavedProblem.user_id == current_user.id).all()
    return [
        {
            "id": s.problem.id,
            "title": s.problem.title,
            "description": s.problem.description,
            "status": s.problem.status.name if s.problem.status else None,
            "created_at": s.problem.created_at
        }
        for s in saved
    ]
