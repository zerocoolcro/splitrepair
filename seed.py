from sqlalchemy.orm import Session
from database import SessionLocal
import models
from auth import hash_password


def seed_admin():
    db: Session = SessionLocal()

    try:
        admin = db.query(models.User).filter(
            models.User.username == "admin"
        ).first()

        if not admin:
            admin = models.User(
                username="admin",
                password=hash_password("admin123"),
                is_admin=1
            )
            db.add(admin)
            db.commit()
            print("✅ Admin user created")
        else:
            print("ℹ️ Admin user already exists")

    finally:
        db.close()
