#!/usr/bin/env python3
"""
Database setup script for LILFIFS
Run this script to create databases and set up user permissions
"""

import mysql.connector

# 
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_databases():
    """Setup databases and user permissions"""
    try:
        # Connect as root to create user and databases
        print("Connecting to MySQL as root...")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')  # Add your root password if needed
        )
        
        if connection.is_connected():
            print("Connected to MySQL as root")
            cursor = connection.cursor()
            
            # Create ilfifs user if not exists
            try:
                cursor.execute("CREATE USER IF NOT EXISTS 'ilfifs'@'localhost' IDENTIFIED BY '1234'")
                print("✅ User 'ilfifs' created or already exists")
            except Error as e:
                print(f"⚠️  Error creating user: {e}")
            
            # Grant privileges to ilfifs user
            try:
                cursor.execute("GRANT ALL PRIVILEGES ON *.* TO 'ilfifs'@'localhost' WITH GRANT OPTION")
                cursor.execute("FLUSH PRIVILEGES")
                print("✅ Privileges granted to 'ilfifs' user")
            except Error as e:
                print(f"⚠️  Error granting privileges: {e}")
            
            # Close root connection
            cursor.close()
            connection.close()
            
            # Test connection as ilfifs user
            print("\nTesting connection as 'ilfifs' user...")
            test_connection = mysql.connector.connect(
                host='localhost',
                user='ilfifs',
                password='1234'
            )
            
            if test_connection.is_connected():
                print("✅ Connection successful as 'ilfifs'")
                cursor = test_connection.cursor()
                
                # Create databases
                databases = [
                    'user_registration_db',
                    'found_items_db', 
                    'lost_items_db',
                    'claimed_items_db',
                    'lostandfound_db'
                ]
                
                for db_name in databases:
                    try:
                        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                        print(f"✅ Database '{db_name}' created or already exists")
                    except Error as e:
                        print(f"❌ Error creating database '{db_name}': {e}")
                
                cursor.close()
                test_connection.close()
                print("\n🎉 Database setup completed successfully!")
                
            else:
                print("❌ Failed to connect as 'ilfifs' user")
                
    except Error as e:
        print(f"❌ Error: {e}")
        print("\n💡 Try running these commands manually:")
        print("mysql -u root -p")
        print("CREATE USER IF NOT EXISTS 'ilfifs'@'localhost' IDENTIFIED BY '1234';")
        print("GRANT ALL PRIVILEGES ON *.* TO 'ilfifs'@'localhost' WITH GRANT OPTION;")
        print("FLUSH PRIVILEGES;")

if __name__ == "__main__":
    setup_databases()
