import os
import sys
import uuid
import csv
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client


def import_roster():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: Supabase admin keys not configured in env.")
        return

    supabase: Client = create_client(supabase_url, supabase_key)

    # Fetch branch rooms to assign users to
    print("Fetching active branch rooms from Supabase...")
    try:
        rooms_res = supabase.table("rooms").select("id").eq("type", "branch").execute()
        branch_room_ids = [r["id"] for r in rooms_res.data]
        print(f"Found {len(branch_room_ids)} branch rooms.")
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

    roster = [
        {"name": "Tamanna", "email": "ayshatamanna96@gmail.com", "phone": "01971319176", "role": "manager", "joining": "20 August 2024", "password": "BiwStaff2000!"},
        {"name": "Akhi Khan", "email": "akhi45651@gmail.com", "phone": "01758679900", "role": "manager", "joining": "28 February 2023", "password": "BiwStaff1998!"},
        {"name": "Nova", "email": "farihanova03@gmail.com", "phone": "01908027282", "role": "manager", "joining": "7 February 2026", "password": "BiwStaff2000!"},
        {"name": "Sharmin Akter", "email": "sharmin07717@gmail.com", "phone": "01883376681", "role": "therapist", "joining": "15 June 2026", "password": "BiwStaff2002!"},
        {"name": "Shahanaj", "email": "doashaharaz93@gmail.com", "phone": "01781874346", "role": "therapist", "joining": "19 April 2026", "password": "BiwStaff2001!"},
        {"name": "Moitree", "email": "mmoitree605@gmail.com", "phone": "01581488173", "role": "therapist", "joining": "11 January 2023", "password": "BiwStaff2002!"},
        {"name": "Rabina", "email": "rabinahaque29@gmail.com", "phone": "01600580204", "role": "therapist", "joining": "11 January 2023", "password": "BiwStaff2002!"},
        {"name": "Anjuman", "email": "anjumanaktar540@gmail.com", "phone": "01320368639", "role": "therapist", "joining": "1 November 2024", "password": "BiwStaff2001!"},
        {"name": "Rima", "email": "darothitripura@gmail.com", "phone": "01318383279", "role": "therapist", "joining": "1 June 2023", "password": "BiwStaff1995!"},
        {"name": "Ajmeri", "email": "angelazmir5060@gmail.com", "phone": "01736715396", "role": "therapist", "joining": "1 November 2025", "password": "BiwStaff2000!"},
        {"name": "Helena", "email": "nitikattripura@gmail.com", "phone": "01840626458", "role": "therapist", "joining": "1 June 2023", "password": "BiwStaff1997!"},
        {"name": "Ishikha", "email": "khumbatripura@gmail.com", "phone": "01627753206", "role": "therapist", "joining": "6 March 2024", "password": "BiwStaff2001!"},
        {"name": "Runa", "email": "sangmarahul604@gmail.com", "phone": "01580738658", "role": "therapist", "joining": "6 March 2024", "password": "BiwStaff1995!"},
        {"name": "Dichi", "email": "dichimree99@gmail.com", "phone": "01722745259", "role": "therapist", "joining": "1 December 2024", "password": "BiwStaff1995!"},
        {"name": "Sobita", "email": "sobitripura98@gmail.com", "phone": "01841152879", "role": "therapist", "joining": "13 October 2025", "password": "BiwStaff1998!"},
        {"name": "Kajoli", "email": "kajolysangma@gmail.com", "phone": "01903411357", "role": "therapist", "joining": "16 October 2025", "password": "BiwStaff1999!"},
        {"name": "Baby", "email": "babysangma650@gmail.com", "phone": "01942904689", "role": "therapist", "joining": "10 June 2025", "password": "BiwStaff2003!"},
        {"name": "Eti", "email": "dofoety@gmail.com", "phone": "01406948581", "role": "therapist", "joining": "17 June 2025", "password": "BiwStaff1997!"},
        {"name": "Sonia", "email": "sonia@biw.com", "phone": "01302540310", "role": "therapist", "joining": "4 February 2026", "password": "BiwStaff1995!"},
        {"name": "Rani", "email": "santitripura687@gmail.com", "phone": "01572707764", "role": "therapist", "joining": "7 November 2024", "password": "BiwStaff2004!"},
        {"name": "Mili", "email": "milimrong357@gmail.com", "phone": "01774709094", "role": "therapist", "joining": "1 December 2024", "password": "BiwStaff1998!"},
        {"name": "Borsha", "email": "borsharunam80@gmail.com", "phone": "01740642824", "role": "therapist", "joining": "11 December 2024", "password": "BiwStaff2005!"},
        {"name": "Lipi", "email": "anikhawee556@gmail.com", "phone": "01610598572", "role": "therapist", "joining": "11 December 2024", "password": "BiwStaff1997!"},
        {"name": "Munni", "email": "titanongrin@gmail.com", "phone": "01992515770", "role": "therapist", "joining": "4 June 2026", "password": "BiwStaff2008!"},
        {"name": "Konika", "email": "khankonika692@gmail.com", "phone": "01340145602", "role": "cleaner", "joining": "6 October 2025", "password": "BiwStaff2007!"},
        {"name": "Popy", "email": "pppju0243@gmail.com", "phone": "01301116582", "role": "cleaner", "joining": "6 October 2025", "password": "BiwStaff2011!"},
        {"name": "Samia", "email": "samiaakterbd2011@gmail.com", "phone": "01839297670", "role": "cleaner", "joining": "25 April 2026", "password": "BiwStaff2005!"},
        {"name": "Takmina", "email": "dhdhdhdjddhh658@gmail.com", "phone": "01863180726", "role": "cleaner", "joining": "25 April 2026", "password": "BiwStaff2007!"}
    ]

    print(f"Roster has {len(roster)} users to process.")
    final_output = []

    # 1. Fetch pre-existing core users to output them in the CSV too
    print("Fetching active core database users...")
    try:
        core_res = supabase.table("employees").select("*").execute()
        for emp in core_res.data:
            if not any(r["email"] == emp["email"] for r in roster):
                # Map to format
                final_output.append({
                    "uid": emp["id"],
                    "name": emp["name"],
                    "email": emp["email"],
                    "password": "Existing Account",
                    "phn_num": "-",
                    "role": emp["role"],
                    "joining_date": "-"
                })
    except Exception as e:
        print(f"Warning fetching existing: {e}")

    # 2. Process roster
    for emp in roster:
        email = emp["email"]
        name = emp["name"]
        role = emp["role"]
        phone = emp["phone"]
        joining = emp["joining"]
        password = emp["password"]

        auth_id = None
        user_exists = False
        
        # Check if already exists in DB
        try:
            check_res = supabase.table("employees").select("id").eq("email", email).execute()
            if check_res.data:
                auth_id = check_res.data[0]["id"]
                user_exists = True
        except Exception as e:
            print(f"Error checking user existence: {e}")
            continue

        if not user_exists:
            print(f"Creating account: {name} ({email})")
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

                # Insert into local DB
                emp_data = {
                    "id": auth_id,
                    "staff_id": staff_id_str,
                    "email": email,
                    "name": name,
                    "role": role,
                    "is_active": True
                }
                supabase.table("employees").insert(emp_data).execute()

                # Assign branch rooms
                memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in branch_room_ids]
                if memberships:
                    supabase.table("room_members").insert(memberships).execute()

            except Exception as e:
                print(f"Failed to create {name}: {e}")
                continue
        else:
            print(f"User {name} ({email}) already exists in database. Updating passwords/room assignments...")
            try:
                # Update password just in case
                supabase.auth.admin.update_user_by_id(auth_id, {"password": password})
                
                # Check room memberships
                m_res = supabase.table("room_members").select("id").eq("employee_id", auth_id).execute()
                if not m_res.data:
                    memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in branch_room_ids]
                    if memberships:
                        supabase.table("room_members").insert(memberships).execute()
            except Exception as e:
                print(f"Error updating existing: {e}")

        # Add to CSV list
        final_output.append({
            "uid": auth_id,
            "name": name,
            "email": email,
            "password": password,
            "phn_num": phone,
            "role": role,
            "joining_date": joining
        })

    # 3. Write CSV file
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "employees_sheet_import.csv")
    print(f"Writing CSV output to: {csv_path}")
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["uid", "name", "email", "password", "phn_num", "role", "joining_date"])
            writer.writeheader()
            for u in final_output:
                writer.writerow(u)
        print("CSV file successfully generated!")
    except Exception as e:
        print(f"Failed to write CSV file: {e}")


if __name__ == "__main__":
    import_roster()
