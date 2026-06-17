from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app import models, schemas

router = APIRouter()

@router.get("", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)) -> Any:
    """
    Get all employees for assignment dropdowns.
    """
    return db.query(models.Employee).filter(models.Employee.is_active == True).all()
