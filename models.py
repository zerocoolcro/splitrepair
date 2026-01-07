from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    is_admin = Column(Integer, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    problems = relationship("Problem", back_populates="user")


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(String)
    longitude = Column(String)
    address = Column(String)


class Status(Base):
    __tablename__ = "statuses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    image_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    status_id = Column(Integer, ForeignKey("statuses.id"))

    user = relationship("User", back_populates="problems")
    location = relationship("Location")
    status = relationship("Status")

    image_url = Column(String, nullable=True)

    status_history = relationship(
        "ProblemStatusHistory",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

class ProblemStatusHistory(Base):
    __tablename__ = "problem_status_history"

    id = Column(Integer, primary_key=True, index=True)

    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    old_status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False)
    new_status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False)

    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)

    # RELATIONS
    problem = relationship("Problem", back_populates="status_history")
    old_status = relationship("Status", foreign_keys=[old_status_id])
    new_status = relationship("Status", foreign_keys=[new_status_id])
    admin = relationship("User")

