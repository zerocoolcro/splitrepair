from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import os, uuid, shutil
from database import get_db
from models import Problem, Status, User, ProblemVote, Location
from auth import get_current_user

router = APIRouter()

@router.post("/problems")
async def create_problem(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filename = None

    if file:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"{upload_dir}/{filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    problem = Problem(
        title=title,
        description=description,
        user_id=current_user.id,
        image_url=filename
    )

    db.add(problem)
    db.commit()
    db.refresh(problem)

    return problem


@router.get("/problems")
def list_problems(
    status: str | None = None,
    search: str | None = None,
    sort: str | None = "new",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Problem).join(Status).join(Location)

    # filter by status
    if status:
        query = query.filter(Status.name == status)

    # search in title + description
    if search:
        query = query.filter(
            or_(
                Problem.title.ilike(f"%{search}%"),
                Problem.description.ilike(f"%{search}%")
            )
        )

    # sorting
    if sort == "new":
        query = query.order_by(Problem.created_at.desc())
    elif sort == "old":
        query = query.order_by(Problem.created_at.asc())
    elif sort == "votes":
        query = (
            query
            .outerjoin(ProblemVote)
            .group_by(Problem.id)
            .order_by(func.count(ProblemVote.id).desc())
        )
    elif sort == "status":
        query = query.order_by(Status.name.asc())

    total = query.count()
    problems = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "lat": p.location.latitude if p.location else None,
                "lng": p.location.longitude if p.location else None,
                "status": p.status.name if p.status else None,
                "created_at": p.created_at,
                "votes": len(p.votes)
            }
            for p in problems
        ]
    }


@router.get("/map/problems")
def get_map_problems(db: Session = Depends(get_db)):
    problems = (
        db.query(Problem)
        .join(Status)
        .join(Location)
        .filter(Status.name != "resolved")
        .all()
    )

    return [
        {
            "id": p.id,
            "title": p.title,
            "lat": p.location.latitude,
            "lng": p.location.longitude,
            "status": p.status.name
        }
        for p in problems
    ]
