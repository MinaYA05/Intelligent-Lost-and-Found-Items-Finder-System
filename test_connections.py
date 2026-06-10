#!/usr/bin/env python3
"""
Test database connections for all databases
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'hawa9')
}

DB_NAMES = {
    'users': os.getenv('DB_NAME_USERS', 'user_registration_db'),
    'found_items': os.getenv('DB_NAME_FOUND_ITEMS', 'found_items_db'), 
    'lost_items': os.getenv('DB_NAME_LOST_ITEMS', 'lost_items_db'),
    'claimed_items': os.getenv('DB_NAME_CLAIMED_ITEMS', 'claimed_items_db'),
    'main': os.getenv('DB_NAME_MAIN', 'lostandfound_db')
}

def test_database_connection(db_name, database):
    """Test connection to a specific database"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = database
        
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            print(f"✅ {db_name:15} -> Connected to '{current_db}' database")
            
            # Test basic operations
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   Tables found: {len(tables)}")
            
            cursor.close()
            connection.close()
            return True
        else:
            print(f"❌ {db_name:15} -> Connection failed")
            return False
            
    except Error as e:
        print(f"❌ {db_name:15} -> Error: {e}")
        return False

def main():
    print("🔍 Testing Database Connections")
    print("=" * 50)
    
    success_count = 0
    total_count = len(DB_NAMES)
    
    for db_name, database in DB_NAMES.items():
        if test_database_connection(db_name, database):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"Results: {success_count}/{total_count} databases connected successfully")
    
    if success_count == total_count:
        print("🎉 All database connections working!")
    else:
        print("⚠️  Some database connections failed. Check permissions.")

if __name__ == "__main__":
    main()
