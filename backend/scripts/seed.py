import os
import sys

# Add the backend directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Room, Employee, RoomMember, RoomType

def seed_database():
    # Only use for dropping all tables to re-seed (dev only)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Seeding database...")

        # 1. Create Rooms (Branches & Departments)
        branches_to_create = [
            "Uttara Ladies",
            "Bashundhara Gents",
            "Bashundhara Ladies"
        ]
        
        departments_to_create = [
            "HR",
            "IT Support",
            "Management"
        ]

        rooms = {}

        # Create Branches
        for branch_name in branches_to_create:
            room = Room(name=branch_name, type=RoomType.branch)
            db.add(room)
            rooms[branch_name] = room
        
        # Create Departments
        for dept_name in departments_to_create:
            room = Room(name=dept_name, type=RoomType.department)
            db.add(room)
            rooms[dept_name] = room
            
        # Create Founder Room
        founder_room = Room(name="Founders", type=RoomType.founder)
        db.add(founder_room)
        rooms["Founders"] = founder_room

        db.commit()

        # 2. Create Dummy Employees for Clinic
        employees = [
            Employee(name="Alice Owner", email="alice@example.com", role="owner"),
            Employee(name="Bob Manager", email="bob@example.com", role="manager"),
            Employee(name="Charlie IT", email="charlie@example.com", role="it_team"),
            Employee(name="Diana HR", email="diana@example.com", role="hr"),
            Employee(name="Eve Therapist", email="eve@example.com", role="therapist"),
            Employee(name="Frank Executive", email="frank@example.com", role="executive"),
            Employee(name="Grace Cleaner", email="grace@example.com", role="cleaner"),
        ]
        db.add_all(employees)
        db.commit()

        # 3. Assign Employees to Rooms
        # Owners and HR are in Management
        db.add(RoomMember(employee_id=employees[0].id, room_id=rooms["Management"].id))
        db.add(RoomMember(employee_id=employees[3].id, room_id=rooms["HR"].id))
        
        # Bob manages Uttara Ladies
        db.add(RoomMember(employee_id=employees[1].id, room_id=rooms["Uttara Ladies"].id))

        # Charlie is in IT
        db.add(RoomMember(employee_id=employees[2].id, room_id=rooms["IT Support"].id))

        # Eve, Frank, Grace are in Uttara Ladies
        db.add(RoomMember(employee_id=employees[4].id, room_id=rooms["Uttara Ladies"].id))
        db.add(RoomMember(employee_id=employees[5].id, room_id=rooms["Uttara Ladies"].id))
        db.add(RoomMember(employee_id=employees[6].id, room_id=rooms["Uttara Ladies"].id))

        db.commit()

        print("Database seeding completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
