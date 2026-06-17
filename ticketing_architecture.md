# Internal Communication & Collaboration System
## Technical Architecture & Implementation Plan

This document translates the theoretical ticketing system into concrete technical specifications tailored to the current stack (FastAPI + SQLAlchemy backend, Next.js frontend).

---

## 1. Database Schema Design (SQLAlchemy Models)

The core principle is to map the room-based privacy and threaded ticketing into relational tables.

### 1.1 `rooms`
Represents a privacy boundary. Can be a Branch, Department, or Founder room.
- `id`: UUID (Primary Key)
- `name`: String (e.g., "Branch A", "HR", "Founder")
- `type`: Enum (`branch`, `department`, `founder`)
- `created_at`: DateTime

### 1.2 `room_members` (Association Table)
Maps employees to the rooms they have access to. 
- `employee_id`: UUID (Foreign Key to `employees.id`)
- `room_id`: UUID (Foreign Key to `rooms.id`)

*(Note: We can also auto-derive room membership dynamically based on the employee's `branch_id` and `role`, but an explicit association table allows for future flexibility like adding specific people to specific task-force rooms).*

### 1.3 `tickets`
The core task/request entity.
- `id`: UUID (Primary Key)
- `title`: String
- `description`: Text
- `creator_id`: UUID (Foreign Key to `employees.id`)
- `assigned_to_id`: UUID, nullable (Foreign Key to `employees.id`)
- `status`: Enum (`open`, `in_progress`, `approved`, `resolved`)
- `priority`: Enum (`low`, `medium`, `high`)
- `due_date`: DateTime, nullable
- `created_at`: DateTime
- `updated_at`: DateTime

### 1.4 `ticket_rooms` (Association Table)
Supports "Cross-Room Tickets" by linking a ticket to one or more rooms.
- `ticket_id`: UUID (Foreign Key)
- `room_id`: UUID (Foreign Key)

### 1.5 `messages`
The atomic units that make up the "Single Thread" model.
- `id`: UUID (Primary Key)
- `ticket_id`: UUID (Foreign Key to `tickets.id`)
- `author_id`: UUID (Foreign Key to `employees.id`)
- `content`: Text
- `type`: Enum (`comment`, `approval`, `status_update`)
- `created_at`: DateTime

---

## 2. Backend API Design (FastAPI)

All endpoints will enforce Row-Level Security based on the `room_members` table. An employee cannot fetch a ticket if it is not associated with at least one room they belong to.

### Room Management
- `GET /api/v1/tickets/rooms`: Returns the list of rooms the authenticated user has access to.

### Ticket Feed
- `GET /api/v1/tickets?room_id={id}`: Returns all tickets associated with a specific room.
- `POST /api/v1/tickets`: Creates a new ticket. Required payload: `title`, `description`, `room_ids` (array).

### Ticket Detail & Threading
- `GET /api/v1/tickets/{id}`: Returns the ticket details, alongside the fully ordered array of `messages`.
- `PATCH /api/v1/tickets/{id}`: Updates status, assignee, or priority.
- `POST /api/v1/tickets/{id}/messages`: Adds a new comment/message to the thread.
- `POST /api/v1/tickets/{id}/assign_rooms`: Adds the ticket to another room (Cross-team coordination).

---

## 3. Frontend Implementation Design (Next.js)

### Layout (`/dashboard/tickets`)
- **Left Sidebar:** Displays the user's accessible Rooms grouped by type (Branches, Departments).
- **Middle Column (Feed):** A list of ticket cards for the currently selected room. Shows title, status badge, and assigned avatars.
- **Right Panel (Detail View):** Clicking a ticket opens the full context.

### The Single Thread View (Ticket Detail)
- **Header:** Title, metadata (Priority, Assigned To), and an action bar to change status.
- **Thread Body:** A chronological, scrollable list of `Message` components.
    - System messages (`status_update` type) will render as small, centered gray text (e.g., *"Manager B changed status to Approved"*).
    - User messages (`comment` type) will render as standard chat bubbles or forum posts.
- **Input Footer:** A sticky text area at the bottom to post a new message.

---

## 4. Phase 1 Execution Plan (Tomorrow's Goals)

1. **Database:** Write the SQLAlchemy model definitions in `backend/app/models/` and generate the Alembic migration to create the tables.
2. **Seeding:** Write a script to auto-generate the base rooms (1 for each existing branch, standard departments) and map existing employees to them based on their current `branch_id` and `role`.
3. **Backend APIs:** Implement the core CRUD routers in `backend/app/api/v1/tickets.py`.
4. **Frontend UI scaffolding:** Create the `/dashboard/tickets` layout with hardcoded dummy data to verify the UX looks good before hooking it up to the API.
5. **Integration:** Connect the Next.js UI to the FastAPI endpoints to achieve a working, end-to-end "Create Ticket -> View Thread -> Post Comment" flow.
