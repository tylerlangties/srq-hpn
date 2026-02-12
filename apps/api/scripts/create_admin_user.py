from __future__ import annotations

import argparse

import app.core.env  # noqa: F401
from app.core.auth import hash_password
from app.db import SessionLocal
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Plain-text password")
    parser.add_argument("--name", default=None, help="Display name")
    args = parser.parse_args()

    email = args.email.strip().lower()
    if not email:
        raise SystemExit("Email is required")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one_or_none()

        if user is None:
            user = User(
                email=email,
                name=args.name,
                role="admin",
                is_active=True,
                auth_provider="local",
                password_hash=hash_password(args.password),
            )
            db.add(user)
            action = "created"
        else:
            user.name = args.name if args.name is not None else user.name
            user.role = "admin"
            user.is_active = True
            user.auth_provider = "local"
            user.password_hash = hash_password(args.password)
            action = "updated"

        db.commit()
        print(f"Admin user {action}: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
