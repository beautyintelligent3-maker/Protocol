from sqlalchemy import text

from app.database import SessionLocal


def enable_realtime():
    db = SessionLocal()
    try:
        print("Enabling realtime for tables...")
        # Supabase uses a publication named 'supabase_realtime'
        # We need to add our tables to it
        tables = ['tickets', 'messages', 'notifications']

        for table in tables:
            # Create a fresh session for each table so errors don't abort the entire block
            table_db = SessionLocal()
            try:
                table_db.execute(text(f"ALTER PUBLICATION supabase_realtime ADD TABLE {table};"))
                table_db.commit()
                print(f"Added {table} to supabase_realtime publication")
            except Exception as e:
                table_db.rollback()
                if 'already added' in str(e).lower() or 'already a member' in str(e).lower():
                    print(f"Table {table} is already in the publication")
                elif 'does not exist' in str(e).lower():
                    print("Publication might not exist. Attempting to create it...")
                    try:
                        table_db.execute(text("CREATE PUBLICATION supabase_realtime FOR ALL TABLES;"))
                        table_db.commit()
                        print("Created supabase_realtime publication")
                    except Exception as ex:
                        table_db.rollback()
                        print(f"Failed to create publication: {ex}")
                else:
                    print(f"Warning for {table}: {e}")
            finally:
                table_db.close()

        db.commit()
        print("Done!")
    finally:
        db.close()

if __name__ == "__main__":
    enable_realtime()
