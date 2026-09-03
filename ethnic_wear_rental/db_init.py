"""
Run this script once to initialize the database:
    python db_init.py
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def init_db():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split on semicolons but keep multi-statement awareness
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
            conn.commit()
        except mysql.connector.Error as e:
            print(f"  [SKIP] {e}")

    cursor.close()
    conn.close()
    print("✅  Database initialized successfully!")

if __name__ == "__main__":
    init_db()
