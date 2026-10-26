"""Create an administrator account from environment variables.

Run after setting ADMIN_EMAIL and ADMIN_PASSWORD in your local environment.
"""
import os

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import User
from app.security import hash_password


def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password or password.startswith("replace-this"):
        raise SystemExit("Set ADMIN_EMAIL and a strong ADMIN_PASSWORD before running this command.")
    if len(password) < 12:
        raise SystemExit("ADMIN_PASSWORD must contain at least 12 characters.")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            raise SystemExit("A user with this email already exists; no changes made.")
        db.add(User(email=email, password_hash=hash_password(password), role="admin"))
        db.commit()
    print(f"Administrator account created for {email}.")


if __name__ == "__main__":
    main()
