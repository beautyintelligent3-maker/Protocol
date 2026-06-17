from typing import Generator, Optional
# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Employee

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# Mock Authentication Dependency
# In a real app, this would extract a JWT token from the Authorization header
# and verify it against Supabase or your auth provider.
def get_current_user(
    x_mock_user: Optional[str] = Header("alice@example.com"),
    db: Session = Depends(get_db)
) -> Employee:
    # Use the email from the header (or default to alice@example.com)
    # to simulate a logged-in user and enforce Row-Level Security.
    user = db.query(Employee).filter(Employee.email == x_mock_user).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mock user not found",
        )
    return user
