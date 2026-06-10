import mysql.connector
import json
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'ilfifs',
    'password': '1234',
    'database': 'lostandfound_db'
}

def check_history():
    try:
        print("Connecting to database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("Checking admin_history table...")
        cursor.execute("SHOW TABLES LIKE 'admin_history'")
        result = cursor.fetchone()
        
        if not result:
            print("❌ admin_history table does NOT exist!")
            return
            
        print("✅ admin_history table exists.")
        
        print("Fetching recent history...")
        cursor.execute("SELECT * FROM admin_history ORDER BY created_at DESC LIMIT 5")
        rows = cursor.fetchall()
        
        if not rows:
            print("No history records found.")
        else:
            for row in rows:
                print(f"ID: {row['id']}, Action: {row['action_type']}, Item: {row['item_type']}, Date: {row['created_at']}")
                
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    check_history()
