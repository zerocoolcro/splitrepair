from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Comment, Problem, Notification, User
from auth import get_current_user
from schemas import CommentOut

router = APIRouter(prefix="/comments", tags=["Comments"])

# --------------------------------------------
# 1️⃣ Dodavanje komentara
# --------------------------------------------
@router.post("/", response_model=CommentOut)
def add_comment(
    problem_id: int,
    text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Kreiranje komentara
    comment = Comment(
        text=text,
        user_id=current_user.id,
        problem_id=problem.id
    )
    db.add(comment)

    # ⚡ Kreiranje notifikacije vlasniku problema (ako komentator nije vlasnik)
    if problem.user_id != current_user.id:
        note = Notification(
            user_id=problem.user_id,
            message=f"Novi komentar na tvoj problem: {problem.title}"
        )
        db.add(note)

    db.commit()
    db.refresh(comment)
    return comment

# --------------------------------------------
# 2️⃣ Dohvat svih komentara za problem
# --------------------------------------------
@router.get("/{problem_id}", response_model=list[CommentOut])
def get_comments(problem_id: int, db: Session = Depends(get_db)):
    comments = (
        db.query(Comment)
        .filter(Comment.problem_id == problem_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return comments
