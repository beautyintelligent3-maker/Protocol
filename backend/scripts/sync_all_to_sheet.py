import os
import sys
import urllib.request
import json
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client

# Explicit phone/joining date mapper for roster users
ROSTER_DETAILS = {
    "ayshatamanna96@gmail.com": {"phone": "01971319176", "joining": "20 August 2024", "password": "BiwStaff2000!"},
    "akhi45651@gmail.com": {"phone": "01758679900", "joining": "28 February 2023", "password": "BiwStaff1998!"},
    "farihanova03@gmail.com": {"phone": "01908027282", "joining": "7 February 2026", "password": "BiwStaff2000!"},
    "sharmin07717@gmail.com": {"phone": "01883376681", "joining": "15 June 2026", "password": "BiwStaff2002!"},
    "doashaharaz93@gmail.com": {"phone": "01781874346", "joining": "19 April 2026", "password": "BiwStaff2001!"},
    "mmoitree605@gmail.com": {"phone": "01581488173", "joining": "11 January 2023", "password": "BiwStaff2002!"},
    "rabinahaque29@gmail.com": {"phone": "01600580204", "joining": "11 January 2023", "password": "BiwStaff2002!"},
    "anjumanaktar540@gmail.com": {"phone": "01320368639", "joining": "1 November 2024", "password": "BiwStaff2001!"},
    "darothitripura@gmail.com": {"phone": "01318383279", "joining": "1 June 2023", "password": "BiwStaff1995!"},
    "angelazmir5060@gmail.com": {"phone": "01736715396", "joining": "1 November 2025", "password": "BiwStaff2000!"},
    "nitikattripura@gmail.com": {"phone": "01840626458", "joining": "1 June 2023", "password": "BiwStaff1997!"},
    "khumbatripura@gmail.com": {"phone": "01627753206", "joining": "6 March 2024", "password": "BiwStaff2001!"},
    "sangmarahul604@gmail.com": {"phone": "01580738658", "joining": "6 March 2024", "password": "BiwStaff1995!"},
    "dichimree99@gmail.com": {"phone": "01722745259", "joining": "1 December 2024", "password": "BiwStaff1995!"},
    "sobitripura98@gmail.com": {"phone": "01841152879", "joining": "13 October 2025", "password": "BiwStaff1998!"},
    "kajolysangma@gmail.com": {"phone": "01903411357", "joining": "16 October 2025", "password": "BiwStaff1999!"},
    "babysangma650@gmail.com": {"phone": "01942904689", "joining": "10 June 2025", "password": "BiwStaff2003!"},
    "dofoety@gmail.com": {"phone": "01406948581", "joining": "17 June 2025", "password": "BiwStaff1997!"},
    "sonia@biw.com": {"phone": "01302540310", "joining": "4 February 2026", "password": "BiwStaff1995!"},
    "santitripura687@gmail.com": {"phone": "01572707764", "joining": "7 November 2024", "password": "BiwStaff2004!"},
    "milimrong357@gmail.com": {"phone": "01774709094", "joining": "1 December 2024", "password": "BiwStaff1998!"},
    "borsharunam80@gmail.com": {"phone": "01740642824", "joining": "11 December 2024", "password": "BiwStaff2005!"},
    "anikhawee556@gmail.com": {"phone": "01610598572", "joining": "11 December 2024", "password": "BiwStaff1997!"},
    "titanongrin@gmail.com": {"phone": "01992515770", "joining": "4 June 2026", "password": "BiwStaff2008!"},
    "khankonika692@gmail.com": {"phone": "01340145602", "joining": "6 October 2025", "password": "BiwStaff2007!"},
    "pppju0243@gmail.com": {"phone": "01301116582", "joining": "6 October 2025", "password": "BiwStaff2011!"},
    "samiaakterbd2011@gmail.com": {"phone": "01839297670", "joining": "25 April 2026", "password": "BiwStaff2005!"},
    "dhdhdhdjddhh658@gmail.com": {"phone": "01863180726", "joining": "25 April 2026", "password": "BiwStaff2007!"}
}


def sync_all():
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    if not webhook_url:
        print("Error: GOOGLE_SHEET_WEBHOOK_URL not set in env.")
        return

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)

    print("Fetching active employees from local database...")
    try:
        res = supabase.table("employees").select("*").eq("is_active", True).execute()
        employees = res.data
        print(f"Found {len(employees)} active employees in DB.")
    except Exception as e:
        print(f"Error: {e}")
        return

    success_count = 0
    error_count = 0

    for emp in employees:
        email = emp["email"]
        uid = emp["id"]
        name = emp["name"]
        role = emp["role"]

        # Cross reference phone / joining / password
        details = ROSTER_DETAILS.get(email, {"phone": "-", "joining": "-", "password": "Existing Account"})
        phone = details["phone"]
        joining = details["joining"]
        password = details["password"]

        # Keep existing password labels for core users
        if email in ["laboni@biw.salon", "usman@biw.salon"]:
            password = "BiwOwner2026!"
        elif email == "khalid@biw.salon":
            password = "BiwBrand2026!"

        payload = {
            "action": "create", # "create" will append or update
            "uid": emp.get("staff_id", uid),
            "email": email,
            "name": name,
            "role": role,
            "password": password,
            "phn_num": phone,
            "joining_date": joining
        }

        print(f"Syncing {name} ({email}) to Google Sheet...")
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                if res_body.get("status") == "success":
                    print(f"  Success: {res_body.get('message')}")
                    success_count += 1
                else:
                    print(f"  Failed: {res_body.get('message')}")
                    error_count += 1
        except Exception as e:
            print(f"  Network Error: {e}")
            error_count += 1

    print("\n--- Webhook Sync Summary ---")
    print(f"Successfully Synced: {success_count}")
    print(f"Failed: {error_count}")


if __name__ == "__main__":
    sync_all()
