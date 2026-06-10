import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'ilfifs'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'database': os.getenv('DB_NAME_USERS', 'user_registration_db')
}

def create_admin():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        admin_email = "minaya@gmail.com"
        admin_password = "minnn"
        # Hash password
        hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        user = cursor.fetchone()
        
        if user:
            print("Admin user already exists. Updating is_admin flag...")
            cursor.execute("UPDATE users SET is_admin = TRUE, role = 'admin' WHERE email = %s", (admin_email,))
        else:
            print("Creating new admin user...")
            query = """
                INSERT INTO users 
                (name, email, phone, address, pincode, dob, password, role, is_admin) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                "Admin User", 
                admin_email, 
                "0000000000", 
                "Admin Office", 
                "000000", 
                "2000-01-01", 
                hashed, 
                "admin", 
                True
            )
            cursor.execute(query, values)
            print("Admin user created successfully.")
            
        conn.commit()
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    create_admin()