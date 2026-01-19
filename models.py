from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, Boolean
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
    votes = relationship("ProblemVote", back_populates="user", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    saved_problems = relationship("SavedProblem", back_populates="user", cascade="all, delete")





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

    comments = relationship("Comment", back_populates="problem", cascade="all, delete")
    votes = relationship("ProblemVote", back_populates="problem", cascade="all, delete")
    saved_by_users = relationship("SavedProblem", back_populates="problem", cascade="all, delete")




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

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    problem_id = Column(Integer, ForeignKey("problems.id"))

    user = relationship("User")
    problem = relationship("Problem", back_populates="comments")

class ProblemVote(Base):
    __tablename__ = "problem_votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    problem_id = Column(Integer, ForeignKey("problems.id"))

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="unique_user_problem_vote"),
    )

    user = relationship("User", back_populates="votes")
    problem = relationship("Problem", back_populates="votes")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class SavedProblem(Base):
    __tablename__ = "saved_problems"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="unique_user_saved_problem"),
    )

    user = relationship("User", back_populates="saved_problems")
    problem = relationship("Problem", back_populates="saved_by_users")
