import os
import sys
import uuid
import re
from html.parser import HTMLParser
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client


class RosterHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.in_td = False
        self.in_tr = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif tag == "td":
            self.in_td = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "tr":
            self.in_tr = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag == "td":
            self.in_td = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_td:
            self.current_cell += data


def parse_roster(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    parser = RosterHTMLParser()
    parser.feed(html_content)

    employees = []
    # Skip the header row
    for row in parser.rows:
        if not row or len(row) < 5:
            continue
        name = row[0]
        phone = row[1]
        email = row[2]
        pin = row[3]
        role_raw = row[4].strip().lower()

        # Skip headers or empty rows
        if name.lower() == "name" or not name:
            continue

        # Normalise email
        email_clean = email
        if not email or "@" not in email or email.lower() == "name":
            # Generate a default safe email
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
            email_clean = f"{safe_name}@biw.com"

        # Map role
        role = "therapist"
        if "manager" in role_raw:
            role = "manager"
        elif "cleaner" in role_raw:
            role = "cleaner"
        elif "nurse" in role_raw:
            role = "therapist"
        elif "therapist" in role_raw:
            role = "therapist"

        employees.append({
            "name": name,
            "phone": phone,
            "email": email_clean,
            "pin": pin,
            "role": role,
            "role_raw": row[4]
        })

    return employees


def bulk_import():
    sheet_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Sheet1.html")
    if not os.path.exists(sheet_path):
        print(f"Error: Sheet1.html not found at {sheet_path}")
        return

    print("Parsing Sheet1.html...")
    employees_to_import = parse_roster(sheet_path)
    print(f"Found {len(employees_to_import)} employees in roster.")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: Supabase admin keys not configured in env.")
        return

    supabase: Client = create_client(supabase_url, supabase_key)

    print("Fetching active branch rooms from Supabase...")
    try:
        rooms_res = supabase.table("rooms").select("id").eq("type", "branch").execute()
        branch_room_ids = [r["id"] for r in rooms_res.data]
        print(f"Found {len(branch_room_ids)} active branch rooms.")
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        return

    # Determine starting staff ID
    print("Fetching highest staff ID from database...")
    try:
        staff_res = supabase.table("employees").select("staff_id").order("staff_id", desc=True).limit(1).execute()
        highest_staff_id = 0
        if staff_res.data and staff_res.data[0]["staff_id"]:
            highest_staff_id = int(staff_res.data[0]["staff_id"])
        print(f"Current highest staff ID: {str(highest_staff_id).zfill(4)}")
    except Exception as e:
        print(f"Error fetching staff ID: {e}")
        return

    imported_count = 0
    memberships_added = 0
    skipped_count = 0

    for emp in employees_to_import:
        email = emp["email"]
        name = emp["name"]
        role = emp["role"]

        # Check if user already exists locally/db
        try:
            check_res = supabase.table("employees").select("id").eq("email", email).execute()
            if check_res.data:
                auth_id = check_res.data[0]["id"]
                # Check if they have memberships assigned
                m_res = supabase.table("room_members").select("id").eq("employee_id", auth_id).execute()
                if not m_res.data:
                    # Missing memberships! Let's assign them.
                    print(f"User {name} exists but is missing room memberships. Assigning branch rooms...")
                    memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in branch_room_ids]
                    if memberships:
                        supabase.table("room_members").insert(memberships).execute()
                        memberships_added += 1
                else:
                    skipped_count += 1
                continue
        except Exception as e:
            print(f"Error checking user existence/memberships: {e}")
            continue

        # Create in Supabase Auth
        temp_password = f"BiwStaff{emp['pin']}!" if emp['pin'].isdigit() else "BiwStaff2026!"
        print(f"Creating account for {name} ({email}) with temp password: {temp_password}")

        try:
            res = supabase.auth.admin.create_user({
                "email": email,
                "password": temp_password,
                "email_confirm": True,
                "user_metadata": {
                    "name": name,
                    "role": role
                }
            })
            auth_id = res.user.id
        except Exception as e:
            print(f"Auth creation failed or user already exists in auth: {e}")
            # Try to list users to find matching email
            try:
                users_res = supabase.auth.admin.list_users()
                user_obj = next((u for u in users_res if u.email == email), None)
                if not user_obj and hasattr(users_res, "users"):
                    user_obj = next((u for u in users_res.users if u.email == email), None)

                if user_obj:
                    auth_id = user_obj.id
                else:
                    print(f"Failed to create or find user: {name} ({email})")
                    skipped_count += 1
                    continue
            except Exception as list_err:
                print(f"Failed to list users: {list_err}")
                skipped_count += 1
                continue

        # Generate staff ID
        highest_staff_id += 1
        staff_id_str = str(highest_staff_id).zfill(4)

        try:
            # Insert employee into database
            emp_data = {
                "id": auth_id,
                "staff_id": staff_id_str,
                "email": email,
                "name": name,
                "role": role,
                "is_active": True
            }
            supabase.table("employees").insert(emp_data).execute()

            # Assign to branch rooms (generate explicit UUID for primary key)
            memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in branch_room_ids]
            if memberships:
                supabase.table("room_members").insert(memberships).execute()

            print(f"Successfully imported {name} as staff ID {staff_id_str} assigned to branch rooms.")
            imported_count += 1
        except Exception as db_err:
            print(f"Failed to insert database record for {name}: {db_err}")
            skipped_count += 1

    print("\n--- Import Summary ---")
    print(f"Successfully imported: {imported_count}")
    print(f"Memberships added to existing: {memberships_added}")
    print(f"Skipped (fully imported): {skipped_count}")


if __name__ == "__main__":
    bulk_import()
