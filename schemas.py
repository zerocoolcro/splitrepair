from pydantic import BaseModel, Field
from fastapi import Form
from typing import Optional
from datetime import datetime


# ----------------------------
# USER SCHEMAS
# ----------------------------

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

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
# RESPONSE
# ----------------------------

class ProblemResponse(BaseModel):
    id: int
    title: str
    description: str
    image_path: str
    created_at: Optional[datetime]
    image_url: Optional[str]
    status: StatusOut

    class Config:
        from_attributes = True
