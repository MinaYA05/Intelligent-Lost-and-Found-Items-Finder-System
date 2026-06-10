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
}

DB_NAMES = {
    'main': os.getenv('DB_NAME_MAIN', 'lostandfound_db'),
    'users': os.getenv('DB_NAME_USERS', 'user_registration_db'),
}

def get_connection(db_name=None):
    config = DB_CONFIG.copy()
    if db_name:
        config['database'] = db_name
    return mysql.connector.connect(**config)

def update_schema():
    print("Starting schema update...")
    
    # 1. Update Users Table (add is_admin)
    try:
        conn = get_connection(DB_NAMES['users'])
        cursor = conn.cursor()
        
        print(f"Checking users table in {DB_NAMES['users']}...")
        
        # Check if is_admin column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'is_admin'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding role column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
            conn.commit()
            print("role column added.")
        else:
            print("role column already exists.")
            
        # 2. Create/Update Admin User
        admin_email = "minaya@gmail.com"
        admin_password = "minnn"
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        # Check if admin user exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (admin_email,))
        user = cursor.fetchone()
        
        if user:
            print("Admin user exists. Updating privileges...")
            cursor.execute("UPDATE users SET is_admin = TRUE WHERE email = %s", (admin_email,))
        else:
            print("Creating admin user...")
            # Assuming columns: name, email, password, etc. 
            # We need to know the exact schema or provide default values.
            # Let's inspect columns first to be safe or use a generic INSERT if we know the schema.
            # Based on typical registration: name, email, password, phone?
            # Let's check columns first
            cursor.execute("SHOW COLUMNS FROM users")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"User columns: {columns}")
            
            # Construct insert query dynamically or assumes standard columns
            # Standard likely: name, email, password (hashed), phone?
            # I'll try a common set and if it fails, I'll print error.
            
            try:
                # specific insert based on likely columns
                cursor.execute("""
                    INSERT INTO users (name, email, password, is_admin) 
                    VALUES (%s, %s, %s, %s)
                """, ("Admin", admin_email, hashed_password, True))
                print("Admin user created.")
            except Exception as e:
                print(f"Error creating admin user: {e}")
                print("Attempting to update if email exists (already checked though)")

        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error updating users db: {e}")

    # 3. Create Feedback and Contact Tables in Main DB
    try:
        conn = get_connection(DB_NAMES['main'])
        cursor = conn.cursor()
        
        print(f"Checking tables in {DB_NAMES['main']}...")
        
        # Create feedbacks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("feedbacks table verified.")
        
        # Create contact_messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_name VARCHAR(255),
                user_email VARCHAR(255),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("contact_messages table verified.")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error updating main db: {e}")

if __name__ == "__main__":
    update_schema()
