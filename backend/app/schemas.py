from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from .models import RoomType, TicketStatus, TicketPriority, MessageType, ApprovalStatus

# --- Auth / User Schemas ---
class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)

# --- Room Schemas ---
class RoomOut(BaseModel):
    id: UUID
    name: str
    type: RoomType
    
    model_config = ConfigDict(from_attributes=True)

# --- Message Schemas ---
class MessageCreate(BaseModel):
    content: str
    type: MessageType = MessageType.comment

class MessageOut(BaseModel):
    id: UUID
    content: str
    type: MessageType
    created_at: datetime
    author: UserOut
    
    model_config = ConfigDict(from_attributes=True)

# --- Ticket Schemas ---
class TicketCreate(BaseModel):
    title: str
    description: str
    room_ids: List[UUID]
    priority: TicketPriority = TicketPriority.medium

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to_id: Optional[UUID] = None
    add_room_id: Optional[UUID] = None

class TicketOut(BaseModel):
    id: UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    approval_status: ApprovalStatus
    created_at: datetime
    updated_at: datetime
    creator: UserOut
    assignee: Optional[UserOut] = None
    rooms: List[RoomOut] = []
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True

class TicketDetailOut(TicketOut):
    messages: List[MessageOut]
    rooms: List[RoomOut]

# --- Notification Schemas ---
class NotificationOut(BaseModel):
    id: UUID
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
