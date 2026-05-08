from pydantic import BaseModel, Field, EmailStr
from fastapi import Form
from typing import Optional, List
from datetime import datetime

# ----------------------------
# USER SCHEMAS
# ----------------------------

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="Email mora biti jedinstven")
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

class ProblemAdminOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    user_id: Optional[int] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----------------------------
# PROBLEM CREATE (Pydantic)
# ----------------------------

class ProblemCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None

# ----------------------------
# FORM DEPENDENCY
# ----------------------------

def ProblemCreateForm(
    title: str = Form(...),
    description: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
) -> ProblemCreate:
    return ProblemCreate(
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        address=address,
    )

# ----------------------------
# STATUS
# ----------------------------

class StatusUpdate(BaseModel):
    status: str


class StatusOut(BaseModel):
    name: str

    class Config:
        from_attributes = True

class StatusHistoryOut(BaseModel):
    old_status: str
    new_status: str
    changed_by: str
    changed_at: datetime

    class Config:
        from_attributes = True

# ----------------------------
# PROBLEM RESPONSE
# ----------------------------

class LocationOut(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]

    class Config:
        from_attributes = True

class ProblemResponse(BaseModel):
    id: int
    title: str
    description: str
    image_path: str
    image_url: Optional[str]
    created_at: Optional[datetime]
    status: StatusOut
    location: Optional[LocationOut]
    user_id: int

    class Config:
        from_attributes = True

# ----------------------------
# PROBLEM LIST RESPONSE
# ----------------------------

class ProblemListItem(BaseModel):
    id: int
    title: str
    description: str
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProblemListResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    next_page: Optional[int]
    prev_page: Optional[int]
    items: List[ProblemResponse]

    class Config:
        from_attributes = True

    


# ----------------------------
# COMMENTS
# ----------------------------

class CommentCreate(BaseModel):
    text: str

class CommentOut(BaseModel):
    id: int
    text: str
    created_at: datetime
    username: str

    class Config:
        from_attributes = True

# ----------------------------
# VOTES
# ----------------------------

class VoteOut(BaseModel):
    problem_id: int
    votes: int

# ----------------------------
# NOTIFICATIONS
# ----------------------------

class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
