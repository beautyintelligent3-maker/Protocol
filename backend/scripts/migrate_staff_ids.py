import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine

def migrate():
    print("Starting staff_id migration...")
    
    with engine.begin() as conn:
        # 1. Add column if it doesn't exist
        print("Ensuring staff_id column exists...")
        conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS staff_id VARCHAR UNIQUE;"))
        
        # 2. Create the sequence
        print("Creating staff_id_seq...")
        conn.execute(text("CREATE SEQUENCE IF NOT EXISTS staff_id_seq START 1;"))

    # 3. Backfill existing employees sequentially
    with SessionLocal() as db:
        print("Fetching employees without staff_id...")
        employees = db.execute(text("SELECT id FROM employees WHERE staff_id IS NULL ORDER BY created_at ASC")).fetchall()
        
        if not employees:
            print("No employees need backfilling.")
        else:
            for emp in employees:
                # Get next sequence value
                seq_val = db.execute(text("SELECT nextval('staff_id_seq')")).scalar()
                # Format as 4-digit zero-padded string
                staff_id_str = str(seq_val).zfill(4)
                
                print(f"Assigning staff_id {staff_id_str} to employee {emp.id}")
                db.execute(
                    text("UPDATE employees SET staff_id = :staff_id WHERE id = :id"),
                    {"staff_id": staff_id_str, "id": emp.id}
                )
            
            db.commit()
            print("Backfill complete.")

if __name__ == "__main__":
    migrate()
