import os
import sys
import uuid
import csv
import urllib.request
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1q2st424hN8qd35vmYjayCpKt9dV9n660k5i-6LJIuOs/gviz/tq?tqx=out:csv"


def sync_from_sheet():
    print(f"Fetching user roster from Google Sheet: {SHEET_CSV_URL}")
    try:
        req = urllib.request.Request(
            SHEET_CSV_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching CSV: {e}")
        return

    # Parse CSV data
    reader = csv.reader(csv_data.splitlines())
    rows = list(reader)
    if not rows:
        print("Error: Empty CSV received.")
        return

    # Log header row info
    header = rows[0]
    print(f"Headers found: {header}")

    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: Supabase admin keys not configured in env.")
        return

    supabase: Client = create_client(supabase_url, supabase_key)

    # Fetch active rooms for membership assignments
    print("Fetching active rooms from Supabase...")
    try:
        rooms_res = supabase.table("rooms").select("*").eq("is_active", True).execute()
        rooms = rooms_res.data
        print(f"Found {len(rooms)} active rooms.")
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        return

    # Fetch highest staff ID
    print("Fetching highest staff ID...")
    try:
        staff_res = supabase.table("employees").select("staff_id").order("staff_id", desc=True).limit(1).execute()
        highest_staff_id = 0
        if staff_res.data and staff_res.data[0]["staff_id"]:
            highest_staff_id = int(staff_res.data[0]["staff_id"])
        print(f"Starting staff ID generation from: {str(highest_staff_id).zfill(4)}")
    except Exception as e:
        print(f"Error fetching staff ID: {e}")
        highest_staff_id = 100

    imported_count = 0
    updated_count = 0
    skipped_count = 0

    # Process each user row (Skip header)
    for index, row in enumerate(rows[1:], start=2):
        if not row or len(row) < 3:
            continue
        
        # Mapping columns: Name (0), Email (1), Role (2), Password (3), Branch/Rooms (4) (optional)
        name = row[0].strip()
        email = row[1].strip()
        role_name = row[2].strip()
        password = row[3].strip() if len(row) > 3 else ""
        branches_raw = row[4].strip() if len(row) > 4 else ""

        if not email or not name or "@" not in email:
            print(f"Row {index}: Skipping invalid row (missing name or email).")
            continue

        # Standardise role string
        role = role_name.lower().replace(" ", "_")
        if "owner" in role:
            role = "owner"
        elif "consultant" in role or "consultation" in role:
            role = "brand_consultant"
        elif "therapist" in role or "nurse" in role:
            role = "therapist"
        elif "manager" in role:
            role = "manager"
        elif "cleaner" in role:
            role = "cleaner"

        # Determine target rooms for the employee
        target_room_ids = []
        if role == "owner":
            # Owners belong to Owners/Management room
            owners_room = next((r for r in rooms if "Owners" in r["name"] or "Management" in r["name"]), None)
            if owners_room:
                target_room_ids.append(owners_room["id"])
        elif branches_raw:
            # If explicit branches are specified in Column 4 (comma-separated list)
            specified_branches = [b.strip().lower() for b in branches_raw.split(",") if b.strip()]
            for room in rooms:
                if room["name"].lower() in specified_branches:
                    target_room_ids.append(room["id"])
        else:
            # Default fallback assignments
            if role == "brand_consultant":
                # Brand consultants see all branches, IT, and HR
                branch_rooms = [r["id"] for r in rooms if r["type"] == "branch"]
                it_rooms = [r["id"] for r in rooms if "IT" in r["name"]]
                hr_rooms = [r["id"] for r in rooms if "HR" in r["name"]]
                target_room_ids = branch_rooms + it_rooms + hr_rooms
            else:
                # All other staff/therapists/cleaners go to all branches by default
                branch_rooms = [r["id"] for r in rooms if r["type"] == "branch"]
                target_room_ids = branch_rooms

        # Check if user already exists
        auth_id = None
        user_exists = False
        try:
            check_res = supabase.table("employees").select("*").eq("email", email).execute()
            if check_res.data:
                auth_id = check_res.data[0]["id"]
                user_exists = True
        except Exception as e:
            print(f"Error checking DB for {email}: {e}")
            continue

        if user_exists:
            # Update existing user
            print(f"Updating existing user: {name} ({email})...")
            try:
                # Sync Auth metadata and password if a password was provided
                update_payload = {"user_metadata": {"name": name, "role": role}}
                if password and "no change" not in password.lower() and "existing" not in password.lower():
                    update_payload["password"] = password
                    print(f"  Updating password for {email}...")

                supabase.auth.admin.update_user_by_id(auth_id, update_payload)

                # Sync local db table
                supabase.table("employees").update({
                    "name": name,
                    "role": role
                }).eq("id", auth_id).execute()

                # Sync room memberships: delete old and add new
                supabase.table("room_members").delete().eq("employee_id", auth_id).execute()
                
                memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in target_room_ids]
                if memberships:
                    supabase.table("room_members").insert(memberships).execute()

                print(f"  Successfully updated {email}.")
                updated_count += 1
            except Exception as e:
                print(f"  Failed to update {email}: {e}")
                skipped_count += 1
        else:
            # Create new user
            if not password or "no change" in password.lower():
                password = "BiwStaff2026!" # Default fallback
            
            print(f"Creating new user: {name} ({email})...")
            try:
                auth_res = supabase.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "name": name,
                        "role": role
                    }
                })
                auth_id = auth_res.user.id

                # Generate staff ID
                highest_staff_id += 1
                staff_id_str = str(highest_staff_id).zfill(4)

                # Insert employee DB record
                emp_data = {
                    "id": auth_id,
                    "staff_id": staff_id_str,
                    "email": email,
                    "name": name,
                    "role": role,
                    "is_active": True
                }
                supabase.table("employees").insert(emp_data).execute()

                # Assign to rooms
                memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in target_room_ids]
                if memberships:
                    supabase.table("room_members").insert(memberships).execute()

                print(f"  Successfully created {email} with staff ID {staff_id_str}.")
                imported_count += 1
            except Exception as e:
                print(f"  Failed to create {email}: {e}")
                skipped_count += 1

    print("\n--- Google Sheet Sync Summary ---")
    print(f"Successfully created: {imported_count}")
    print(f"Successfully updated: {updated_count}")
    print(f"Errors/Skipped: {skipped_count}")


if __name__ == "__main__":
    sync_from_sheet()
