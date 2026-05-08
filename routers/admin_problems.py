from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from database import get_db
from models import Problem, Status, User, Notification, ProblemStatusHistory, Location
from auth import get_current_user
from schemas import ProblemAdminOut, StatusHistoryOut, StatusUpdate
from datetime import datetime, timedelta

admin_problems_router = APIRouter(
    prefix="/admin/problems",
    tags=["Admin - Problems"]
)

# ---------------- ADMIN CHECK ----------------

def admin_required(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user


# -----------------------------------------------------
# 1) LISTA SVIH PROBLEMA (FIXED)
# -----------------------------------------------------
@admin_problems_router.get("/", response_model=list[ProblemAdminOut])
def list_all_problems(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    problems = (
        db.query(Problem)
        .join(Status)
        .all()
    )

    result = []

    for problem in problems:
        result.append(
            ProblemAdminOut(
                id=problem.id,
                title=problem.title,
                description=problem.description,
                status=problem.status.name if problem.status else "unknown",
                user_id=problem.user_id,
                image_url=problem.image_path,
                created_at=problem.created_at,
            )
        )

    return result


# ------------------------------------------------------
#  ADMIN STATS
# ------------------------------------------------------

@admin_problems_router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    total = db.query(Problem).count()

    open_count = db.query(Problem).join(Status).filter(Status.name == "open").count()
    pending_count = db.query(Problem).join(Status).filter(Status.name == "pending").count()
    resolved_count = db.query(Problem).join(Status).filter(Status.name == "resolved").count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    today_count = (
        db.query(Problem)
        .filter(Problem.created_at >= today_start)
        .count()
    )

    top_users = (
        db.query(User.username, func.count(Problem.id))
        .join(Problem, Problem.user_id == User.id)
        .group_by(User.username)
        .order_by(func.count(Problem.id).desc())
        .limit(5)
        .all()
    )

    top_locations = (
        db.query(Location.address, func.count(Problem.id))
        .join(Problem, Problem.location_id == Location.id)
        .group_by(Location.address)
        .order_by(func.count(Problem.id).desc())
        .limit(5)
        .all()
    )

    # WEEKLY GROWTH
    week_start = datetime.utcnow() - timedelta(days=7)
    prev_week_start = datetime.utcnow() - timedelta(days=14)

    this_week = (
        db.query(Problem)
        .filter(Problem.created_at >= week_start)
        .count()
    )

    last_week = (
        db.query(Problem)
        .filter(
            Problem.created_at >= prev_week_start,
            Problem.created_at < week_start
        )
        .count()
    )

    growth = 0
    if last_week > 0:
        growth = round(((this_week - last_week) / last_week) * 100, 2)


    return {
        "total": total,
        "open": open_count,
        "pending": pending_count,
        "resolved": resolved_count,
        "today": today_count,
        "top_users": [{"username": u, "count": c} for u, c in top_users],
        "top_locations": [{"location": l, "count": c} for l, c in top_locations],
        "growth": growth,
    }


@admin_problems_router.get("/stats/trend")
def problems_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    from sqlalchemy import func

    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    data = (
        db.query(
            func.date(Problem.created_at).label("date"),
            func.count(Problem.id)
        )
        .filter(Problem.created_at >= seven_days_ago)
        .group_by(func.date(Problem.created_at))
        .order_by(func.date(Problem.created_at))
        .all()
    )

    return [
        {"date": str(d), "count": c}
        for d, c in data
    ]

# -----------------------------------------------------
# 2) PROMJENA STATUSA
# -----------------------------------------------------
@admin_problems_router.patch("/{problem_id}/status")
def update_problem_status(
    problem_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    status_name = data.status.lower()

    new_status = db.query(Status).filter(Status.name == status_name).first()
    if not new_status:
        raise HTTPException(status_code=400, detail="Invalid status")

    old_status_id = problem.status_id

    if old_status_id == new_status.id:
        return {"message": "Status already set"}

    history = ProblemStatusHistory(
        problem_id=problem.id,
        old_status_id=old_status_id,
        new_status_id=new_status.id,
        changed_by=current_user.id,
        changed_at=datetime.utcnow()
    )
    db.add(history)

    problem.status_id = new_status.id

    db.add(
        Notification(
            user_id=problem.user_id,
            message=f"Status tvog problema '{problem.title}' promijenjen je u {new_status.name}"
        )
    )

    db.commit()
    return {"message": "Status updated"}



# -----------------------------------------------------
# 3) POVIJEST STATUSA
# -----------------------------------------------------
@admin_problems_router.get("/{problem_id}/status-history", response_model=list[StatusHistoryOut])
def get_problem_status_history(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    history = (
        db.query(ProblemStatusHistory)
        .filter(ProblemStatusHistory.problem_id == problem_id)
        .order_by(ProblemStatusHistory.changed_at.desc())
        .all()
    )

    result = []
    for h in history:
        old_status = db.query(Status).filter(Status.id == h.old_status_id).first()
        new_status = db.query(Status).filter(Status.id == h.new_status_id).first()
        admin = db.query(User).filter(User.id == h.changed_by).first()

        result.append(
            StatusHistoryOut(
                old_status=old_status.name if old_status else "unknown",
                new_status=new_status.name if new_status else "unknown",
                changed_by=admin.username if admin else "unknown",
                changed_at=h.changed_at,
            )
        )

    return result


# -----------------------------------------------------
# 4) DELETE
# -----------------------------------------------------
@admin_problems_router.delete("/{problem_id}")
def delete_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    db.delete(problem)
    db.commit()

    return {"message": "Problem deleted"}

