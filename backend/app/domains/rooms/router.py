from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user, get_db

router = APIRouter()


@router.get("/all", response_model=List[schemas.RoomOut])
def get_all_rooms(db: Session = Depends(get_db)) -> Any:
    """
    Get all active rooms for escalation dropdowns.
    """
    return db.query(models.Room).filter(models.Room.is_active == True).all()


@router.post("", response_model=schemas.RoomOut)
def create_room(
    room_in: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Create a new room. Owner only.
    """
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create rooms")

    valid_types = [t.value for t in models.RoomType]
    if room_in.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid room type. Must be one of: {valid_types}",
        )

    room_type = models.RoomType[room_in.type]
    room = models.Room(name=room_in.name, type=room_type)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room
