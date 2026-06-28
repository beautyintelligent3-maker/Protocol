from typing import Generator

# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Employee


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> Employee:
    token = credentials.credentials
    jwt_secret = settings.SUPABASE_JWT_SECRET

    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured on the server",
        )

    from supabase import Client, create_client

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
    supabase: Client = create_client(supabase_url, supabase_key)

    try:
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token: missing subject",
            )
        user_id_str = user_res.user.id

        import uuid

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            print("Supabase auth failed: malformed subject UUID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token: malformed subject",
            )

        # Recreate a pseudo payload for the JIT logic
        payload = {"email": user_res.user.email, "user_metadata": user_res.user.user_metadata or {}}

    except Exception as e:
        print(f"Supabase auth failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )

    user = db.query(Employee).filter(Employee.id == user_id).first()
    if not user:
        # Just-in-time provisioning / relinking
        email = payload.get("email")
        if not email:
            print(f"User with ID {user_id} not found in database and no email in JWT")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
            )

        # If user recreated their account, link by email
        existing_user = db.query(Employee).filter(Employee.email == email).first()
        if existing_user:
            # Update their ID to the new Supabase Auth UUID
            existing_user.id = user_id
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            # Create completely new employee record
            from sqlalchemy import text

            max_id = db.execute(text(
                "SELECT COALESCE(MAX(CAST(staff_id AS INTEGER)), 0) FROM employees WHERE staff_id ~ '^[0-9]+$'"
            )).scalar()
            staff_id_str = str(max_id + 1).zfill(4)

            user_metadata = payload.get("user_metadata", {})
            name = user_metadata.get("name", email.split("@")[0])
            role = user_metadata.get("role", "executive")

            user = Employee(id=user_id, staff_id=staff_id_str, email=email, name=name, role=role)
            db.add(user)
            db.commit()
            db.refresh(user)
    if not user.is_active:
        print(f"User with ID {user_id} is deactivated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )
    return user
