import mysql.connector
from app import get_db_connection

def check_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("--- Tables ---")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
        
    print("\n--- Users Table Columns ---")
    try:
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]} - {col[1]}")
    except:
        print("users table not found")

    print("\n--- Checking for feedback/contact tables ---")
    expected_tables = ['feedbacks', 'contact_messages']
    for t in expected_tables:
        if (t,) in tables:
             print(f"{t} exists")
             cursor.execute(f"DESCRIBE {t}")
             for col in cursor.fetchall():
                 print(f"  {col[0]} - {col[1]}")
        else:
             print(f"{t} does NOT exist")

    conn.close()

if __name__ == "__main__":
    check_schema()
