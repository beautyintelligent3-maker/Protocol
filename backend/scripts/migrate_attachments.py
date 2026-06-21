import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load env vars from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(DATABASE_URL)


def migrate():
    with engine.connect() as conn:
        try:
            print("Adding attachment_name column...")
            conn.execute(text("ALTER TABLE messages ADD COLUMN attachment_name VARCHAR;"))
        except Exception as e:
            print(f"Error (maybe exists): {e}")

        try:
            print("Adding attachment_type column...")
            conn.execute(text("ALTER TABLE messages ADD COLUMN attachment_type VARCHAR;"))
        except Exception as e:
            print(f"Error (maybe exists): {e}")

        try:
            print("Adding attachment_data column...")
            conn.execute(text("ALTER TABLE messages ADD COLUMN attachment_data BYTEA;"))
        except Exception as e:
            print(f"Error (maybe exists): {e}")

        conn.commit()
        print("Migration complete!")


if __name__ == "__main__":
    migrate()
