from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app import models, schemas

router = APIRouter()

@router.get("/me", response_model=schemas.UserOut)
def get_current_user_profile(
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Get current logged in user profile.
    """
    return current_user

@router.get("", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)) -> Any:
    """
    Get all employees for assignment dropdowns.
    """
    return db.query(models.Employee).filter(models.Employee.is_active == True).all()

import os
from supabase import create_client, Client
from fastapi import HTTPException, status
import uuid

@router.post("", response_model=schemas.UserOut)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Create new staff user. Only Owners can create accounts.
    """
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create new staff accounts")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase admin keys not configured")

    supabase_admin: Client = create_client(supabase_url, supabase_key)

    try:
        # Create user in Supabase Auth
        # Admin API bypasses signup restrictions and email confirmation
        res = supabase_admin.auth.admin.create_user({
            "email": user_in.email,
            "password": user_in.password,
            "email_confirm": True,
            "user_metadata": {"name": user_in.name, "role": user_in.role}
        })
        
        new_uuid = res.user.id
        
        # Create Employee in local DB with exactly the same UUID
        employee = models.Employee(
            id=uuid.UUID(new_uuid),
            email=user_in.email,
            name=user_in.name,
            role=user_in.role
        )
        db.add(employee)
        
        # Link to the selected room
        room_membership = models.RoomMember(employee_id=employee.id, room_id=user_in.room_id)
        db.add(room_membership)
        
        db.commit()
        db.refresh(employee)
        return employee

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
