from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Problem, SavedProblem
from auth import get_current_user

router = APIRouter(prefix="/saved", tags=["Saved Problems"])

# ✅ Dodaj problem u favorites
@router.post("/{problem_id}")
def save_problem(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter_by(id=problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    exists = db.query(SavedProblem).filter_by(user_id=current_user.id, problem_id=problem_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="Problem already saved")

    saved = SavedProblem(user_id=current_user.id, problem_id=problem_id)
    db.add(saved)
    db.commit()
    return {"message": "Problem saved"}

# ✅ Ukloni problem iz favorites
@router.delete("/{problem_id}")
def unsave_problem(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    saved = db.query(SavedProblem).filter_by(user_id=current_user.id, problem_id=problem_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved problem not found")

    db.delete(saved)
    db.commit()
    return {"message": "Problem removed from saved"}

# ✅ Lista svih spremljenih problema korisnika
@router.get("/", response_model=list[dict])
def list_saved_problems(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    saved = db.query(SavedProblem).filter_by(user_id=current_user.id).all()
    return [
        {
            "id": s.problem.id,
            "title": s.problem.title,
            "description": s.problem.description,
            "status": s.problem.status.name,
            "lat": s.problem.location.latitude,
            "lng": s.problem.location.longitude,
            "created_at": s.problem.created_at
        }
        for s in saved
    ]
