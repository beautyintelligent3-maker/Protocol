import os
import sys

# Add the backend directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Employee, Room, Ticket, TicketPriority, TicketRoom, TicketStatus


def seed_tickets():
    db = SessionLocal()
    try:
        print("Seeding mock tickets...")

        # Get Alice Manager
        alice = db.query(Employee).filter(Employee.email == "alice@example.com").first()
        # Get Bob Staff
        bob = db.query(Employee).filter(Employee.email == "bob@example.com").first()

        # Get Rooms
        uttara = db.query(Room).filter(Room.name == "Uttara Ladies").first()
        management = db.query(Room).filter(Room.name == "Management").first()
        bashundhara = db.query(Room).filter(Room.name == "Bashundhara Gents").first()

        if not alice or not uttara:
            print("Base data not found. Please run seed.py first.")
            return

        # Create Ticket 1
        t1 = Ticket(
            title="Need new AC unit for the lobby",
            description="The current AC unit in the Uttara branch lobby is making a loud noise and not cooling properly. Please send maintenance.",
            priority=TicketPriority.high,
            status=TicketStatus.open,
            creator_id=alice.id,
        )
        db.add(t1)
        db.flush()
        db.add(TicketRoom(ticket_id=t1.id, room_id=uttara.id))

        # Create Ticket 2
        t2 = Ticket(
            title="Monthly performance review templates",
            description="Can someone from Management share the updated template for the monthly performance reviews? We need to start filling them out for Q2.",
            priority=TicketPriority.medium,
            status=TicketStatus.in_progress,
            creator_id=bob.id,
        )
        db.add(t2)
        db.flush()
        db.add(TicketRoom(ticket_id=t2.id, room_id=management.id))
        # This is a cross-room ticket (Bob is in Bashundhara, asking Management)
        db.add(TicketRoom(ticket_id=t2.id, room_id=bashundhara.id))

        # Create Ticket 3
        t3 = Ticket(
            title="Request for leave approval",
            description="I would like to request 3 days of leave next month for a family event.",
            priority=TicketPriority.low,
            status=TicketStatus.resolved,
            creator_id=alice.id,
        )
        db.add(t3)
        db.flush()
        db.add(TicketRoom(ticket_id=t3.id, room_id=management.id))
        db.add(TicketRoom(ticket_id=t3.id, room_id=uttara.id))

        # 4. Seed Notifications
        from app.models import Notification

        db.add(
            Notification(
                user_id=bob.id,
                message="Reminder: You have 1 unassigned high-priority ticket awaiting review in your branch.",
                is_read=False,
            )
        )
        db.add(
            Notification(
                user_id=bob.id,
                message="Alice Owner approved the monthly template task.",
                is_read=True,
            )
        )
        db.add(
            Notification(
                user_id=alice.id,
                message="Bob Manager created a new task requiring your approval.",
                is_read=False,
            )
        )

        db.commit()
        print("Successfully seeded 3 mock tickets!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_tickets()
