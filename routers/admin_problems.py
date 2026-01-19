from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Problem, Status, User, Notification, ProblemStatusHistory
from auth import get_current_user
from schemas import ProblemResponse, StatusHistoryOut
from datetime import datetime

admin_problems_router = APIRouter(
    prefix="/admin/problems",
    tags=["Admin - Problems"],
    dependencies=[Depends(get_current_user)]
)



def admin_required(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user


# -----------------------------------------------------
# 1) LISTA SVIH PROBLEMA
# -----------------------------------------------------
@admin_problems_router.get("/", response_model=list[ProblemResponse])
def list_all_problems(db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    return db.query(Problem).order_by(Problem.created_at.desc()).all()


# -----------------------------------------------------
# 2) PROMJENA STATUSA PROBLEMA
# -----------------------------------------------------
@admin_problems_router.patch("/{problem_id}/status")
def update_problem_status(
    problem_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user = Depends(admin_required)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    new_status = db.query(Status).filter(Status.name == status).first()
    if not new_status:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Must be: open, pending, resolved"
        )

    old_status_id = problem.status_id

    # ⛔ nema promjene — nema zapisa
    if old_status_id == new_status.id:
        return {"message": "Status already set", "status": status}

    # ✅ ZAPIŠI POVIJEST
    history = ProblemStatusHistory(
        problem_id=problem.id,
        old_status_id=old_status_id,
        new_status_id=new_status.id,
        changed_by=current_user.id,
        changed_at=datetime.utcnow()
    )
    db.add(history)

    # ✅ PROMIJENI STATUS
    problem.status_id = new_status.id
    note = Notification(
        user_id=problem.user_id,
        message=f"Status tvog problema '{problem.title}' je promijenjen u {new_status.name}"
    )
    db.add(note)
    db.commit()
    db.refresh(problem)

    return {
        "message": "Status updated",
        "problem_id": problem.id,
        "old_status_id": old_status_id,
        "new_status": status
    }

@admin_problems_router.get("/problems/{problem_id}/status-history", response_model=list[StatusHistoryOut])
def get_problem_status_history(problem_id: int, db: Session = Depends(get_db)):
    history = (
        db.query(ProblemStatusHistory)
        .filter(ProblemStatusHistory.problem_id == problem_id)
        .order_by(ProblemStatusHistory.changed_at.desc())
        .all()
    )

    return [
        StatusHistoryOut(
            old_status=h.old_status.name,
            new_status=h.new_status.name,
            changed_by=h.admin.username,
            changed_at=h.changed_at,
        )
        for h in history
    ]



# -----------------------------------------------------
# 3) BRISANJE PROBLEMA
# -----------------------------------------------------
@admin_problems_router.delete("/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    db.delete(problem)
    db.commit()

    return {"message": "Problem deleted"}

