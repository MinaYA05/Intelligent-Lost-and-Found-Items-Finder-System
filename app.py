#run "py app.py or python app.py" in terminal whenever you want to run this python commands
#pip install flask flask-cors mysql-connector-python bcrypt

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from functools import wraps
import mysql.connector
from mysql.connector import Error
import bcrypt
import os
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import re
from werkzeug.utils import secure_filename
import uuid
import math
import json
from collections import Counter, defaultdict
import jwt
from ml_model import ml_system

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Configure session to work properly
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Allow cross-origin
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow all domains
app.config['SESSION_COOKIE_PATH'] = '/'  # Available on all paths
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime

# Get allowed origins from env
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://127.0.0.1:5000').split(',')
CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS, expose_headers=['Content-Type', 'Set-Cookie'], allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Cookie'])

# JWT Authentication Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', app.secret_key)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(hours=24)

def create_session_token(user_id, user_name, user_email, is_admin=False):
    """Create a JWT token"""
    payload = {
        'user_id': user_id,
        'user_name': user_name,
        'user_email': user_email,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA,
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def validate_session_token(token):
    """Validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def delete_session_token(token):
    # JWT is stateless, so we don't need to delete it from server
    # Client should discard the token
    pass

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'founditems')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve frontend files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'ilfifs'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'database': os.getenv('DB_NAME_MAIN', 'lostandfound_db')  # Main database
}

# Database names for different purposes
DB_NAMES = {
    'main': os.getenv('DB_NAME_MAIN', 'lostandfound_db'),
    'users': os.getenv('DB_NAME_USERS', 'user_registration_db'),
    'found_items': os.getenv('DB_NAME_FOUND_ITEMS', 'found_items_db'), 
    'lost_items': os.getenv('DB_NAME_LOST_ITEMS', 'lost_items_db'),
    'claimed_items': os.getenv('DB_NAME_CLAIMED_ITEMS', 'claimed_items_db')
}

def create_db_connection():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def create_server_connection():
    try:
        config_no_db = DB_CONFIG.copy()
        config_no_db.pop('database', None)
        connection = mysql.connector.connect(**config_no_db)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Server: {e}")
        return None

def ensure_search_weights_schema(cursor):
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'search_weights' AND COLUMN_NAME = %s
    """, (DB_NAMES['main'], 'category'))
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE search_weights ADD COLUMN category VARCHAR(100)")

    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'search_weights' AND COLUMN_NAME = %s
    """, (DB_NAMES['main'], 'usage_count'))
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE search_weights ADD COLUMN usage_count INT DEFAULT 1")

    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'search_weights' AND COLUMN_NAME = %s
    """, (DB_NAMES['main'], 'success_rate'))
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE search_weights ADD COLUMN success_rate DECIMAL(5,3) DEFAULT 0.000")

    cursor.execute("""
        SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS cols, NON_UNIQUE
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'search_weights'
        GROUP BY INDEX_NAME, NON_UNIQUE
    """, (DB_NAMES['main'],))
    indexes = cursor.fetchall()
    for index_name, cols, non_unique in indexes:
        if non_unique == 0 and index_name != 'PRIMARY' and cols == 'term':
            cursor.execute(f"ALTER TABLE search_weights DROP INDEX {index_name}")
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'search_weights' AND INDEX_NAME = 'term_category_unique'
    """, (DB_NAMES['main'],))
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE search_weights ADD UNIQUE INDEX term_category_unique (term, category)")

def ensure_users_schema(cursor):
    """Ensure users table has all required columns"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'profile_pic'
    """, (DB_NAMES['users'],))
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(255)")
        print("Added profile_pic column to users table")

def init_database():
    """Initialize database and create tables if they don't exist"""
    try:
        # Connect without specifying database to create databases
        config_no_db = DB_CONFIG.copy()
        del config_no_db['database']
        
        connection = mysql.connector.connect(**config_no_db)
        cursor = connection.cursor()
        
        # Create all databases
        for db_name in DB_NAMES.values():
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"Database {db_name} created or already exists")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Now connect to main database and create tables
        connection = create_db_connection()
        if connection is None:
            return False
            
        cursor = connection.cursor()
        
        # Create users table in user_registration_db
        cursor.execute(f"USE {DB_NAMES['users']}")
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20) UNIQUE NOT NULL,
            address TEXT,
            pincode VARCHAR(10),
            dob DATE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_users_table)
        ensure_users_schema(cursor)
        
        # Create found_items table in found_items_db
        cursor.execute(f"USE {DB_NAMES['found_items']}")
        create_found_items_table = """
        CREATE TABLE IF NOT EXISTS found_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            location_found VARCHAR(255) NOT NULL,
            date_found DATE NOT NULL,
            category VARCHAR(100) NOT NULL,
            image_path VARCHAR(255) NOT NULL,
            reported_by INT NOT NULL,
            status ENUM('available', 'claimed', 'disposed') DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_found_items_table)
        
        # Create lost_items table in lost_items_db
        cursor.execute(f"USE {DB_NAMES['lost_items']}")
        create_lost_items_table = """
        CREATE TABLE IF NOT EXISTS lost_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            location_lost VARCHAR(255) NOT NULL,
            date_lost DATE NOT NULL,
            category VARCHAR(100) NOT NULL,
            image_path VARCHAR(255),
            reported_by INT NOT NULL,
            status ENUM('lost', 'found', 'recovered') DEFAULT 'lost',
            found_item_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_lost_items_table)
        
        # Create claimed_items table in claimed_items_db
        cursor.execute(f"USE {DB_NAMES['claimed_items']}")
        create_claimed_items_table = """
        CREATE TABLE IF NOT EXISTS claimed_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            original_found_item_id INT,
            item_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            location_found VARCHAR(255) NOT NULL,
            date_found DATE NOT NULL,
            category VARCHAR(100) NOT NULL,
            image_path VARCHAR(255) NOT NULL,
            reported_by INT,
            claimed_by INT,
            date_claimed DATE NOT NULL,
            claim_notes TEXT,
            verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_claimed_items_table)

        # Create claim_requests table for general claim inquiries
        create_claim_requests_table = """
        CREATE TABLE IF NOT EXISTS claim_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            claimant_name VARCHAR(255) NOT NULL,
            claimant_email VARCHAR(255) NOT NULL,
            item_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            location_lost VARCHAR(255) NOT NULL,
            found_item_id INT,
            status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_claim_requests_table)

        # Create found_requests table for lost items (when someone finds a lost item)
        create_found_requests_table = """
        CREATE TABLE IF NOT EXISTS found_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            finder_name VARCHAR(255) NOT NULL,
            finder_email VARCHAR(255) NOT NULL,
            item_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            location_found VARCHAR(255) NOT NULL,
            lost_item_id INT,
            status ENUM('pending', 'contacted', 'resolved') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_found_requests_table)
        
        # Create search_feedback table in main database
        cursor.execute(f"USE {DB_NAMES['main']}")
        create_search_feedback_table = """
        CREATE TABLE IF NOT EXISTS search_feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_query TEXT NOT NULL,
            item_id INT,
            relevance_score INT NOT NULL,
            user_id INT,
            interaction_type ENUM('view', 'claim', 'skip') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_search_feedback_table)
        
        # Create search_weights table in main database
        create_search_weights_table = """
        CREATE TABLE IF NOT EXISTS search_weights (
            id INT AUTO_INCREMENT PRIMARY KEY,
            term VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            weight DECIMAL(5,3) DEFAULT 1.000,
            usage_count INT DEFAULT 1,
            success_rate DECIMAL(5,3) DEFAULT 0.000,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY (term, category)
        )
        """
        cursor.execute(create_search_weights_table)
        ensure_search_weights_schema(cursor)
        
        # Create feedbacks table in main database
        create_feedbacks_table = """
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_feedbacks_table)

        # Create contact_messages table in main database
        create_contact_messages_table = """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_name VARCHAR(255),
            user_email VARCHAR(255),
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_contact_messages_table)

        # Create admin_history table in main database
        create_admin_history_table = """
        CREATE TABLE IF NOT EXISTS admin_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            action_type VARCHAR(50) NOT NULL,
            item_type VARCHAR(50) NOT NULL,
            item_id INT,
            details TEXT,
            admin_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_admin_history_table)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("All databases and tables created successfully!")
        return True
        
    except Error as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def import_existing_images(cursor):
    """Import existing images from founditems folder into database"""
    try:
        founditems_path = 'founditems'
        if os.path.exists(founditems_path):
            image_files = [f for f in os.listdir(founditems_path) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            
            for image_file in image_files:
                # Check if image already exists in database
                cursor.execute("SELECT id FROM found_items WHERE image_path = %s", (image_file,))
                if not cursor.fetchone():
                    # Add to database with default values
                    item_name = image_file.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
                    cursor.execute("""
                        INSERT INTO found_items (item_name, description, location_found, date_found, category, image_path, reported_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_name,
                        f"Found item: {item_name}",
                        "Unknown",
                        datetime.now().date(),
                        "Others",
                        image_file,
                        0
                    ))
                    print(f"Imported existing image: {image_file}")
            
            if image_files:
                print(f"Imported {len(image_files)} existing images to database")
                
    except Exception as e:
        print(f"Error importing existing images: {e}")

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number"""
    pattern = r'^[0-9]{10}$'
    return re.match(pattern, str(phone)) is not None

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        # Handle both JSON and form data (for file upload)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        # Validate required fields
        required_fields = ['name', 'email', 'phonenum', 'pass', 'cpass']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate passwords match
        if data['pass'] != data['cpass']:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Validate phone number
        if not validate_phone(data['phonenum']):
            return jsonify({'success': False, 'message': 'Phone number must be 10 digits'}), 400
        
        # Handle profile image upload
        profile_pic_path = None
        if 'profile' in request.files:
            file = request.files['profile']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create profiles directory if not exists
                profiles_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles')
                if not os.path.exists(profiles_dir):
                    os.makedirs(profiles_dir)
                
                # Unique filename
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(profiles_dir, unique_filename)
                file.save(file_path)
                
                # Store path relative to root (web accessible)
                # Using forward slashes for web compatibility
                profile_pic_path = f"{app.config['UPLOAD_FOLDER']}/profiles/{unique_filename}"
        
        # Hash password
        hashed_password = bcrypt.hashpw(data['pass'].encode('utf-8'), bcrypt.gensalt())
        
        # Connect to users database
        config_users = DB_CONFIG.copy()
        config_users['database'] = DB_NAMES['users']
        
        connection = mysql.connector.connect(**config_users)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor()
            
            # Check if user already exists
            check_query = "SELECT id FROM users WHERE email = %s OR phone = %s"
            cursor.execute(check_query, (data['email'], data['phonenum']))
            existing_user = cursor.fetchone()
            
            if existing_user:
                return jsonify({'success': False, 'message': 'User with this email or phone already exists'}), 409
            
            # Insert new user
            insert_query = """
            INSERT INTO users (name, email, phone, address, pincode, dob, password, profile_pic)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            user_data = (
                data['name'],
                data['email'],
                data['phonenum'],
                data.get('address', ''),
                data.get('pincode', ''),
                data.get('dob', None),
                hashed_password.decode('utf-8'),
                profile_pic_path
            )
            
            cursor.execute(insert_query, user_data)
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Registration successful! Please login.',
                'user_id': cursor.lastrowid
            }), 201
            
        except Error as e:
            print(f"Error during registration: {e}")
            return jsonify({'success': False, 'message': 'Registration failed'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Unexpected error during registration: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    print("=== LOGIN ATTEMPT ===")
    try:
        print("Getting request data...")
        data = request.get_json()
        print(f"Login data received: {data}")
        
        if not data:
            print("No data received in request")
            return jsonify({'success': False, 'message': 'No data received'}), 400
        
        if not data.get('email_mob') or not data.get('pass'):
            print("Missing email/phone or password")
            return jsonify({'success': False, 'message': 'Email/phone and password are required'}), 400
        
        print("Creating database connection...")
        # Connect to users database
        config_users = DB_CONFIG.copy()
        config_users['database'] = DB_NAMES['users']
        
        connection = mysql.connector.connect(**config_users)
        if connection is None:
            print("Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        print("Database connection successful")
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Check if input is email or phone
            login_field = data['email_mob']
            print(f"Login field: {login_field}")
            
            if validate_email(login_field):
                query = "SELECT * FROM users WHERE email = %s"
                print("Using email query")
            else:
                query = "SELECT * FROM users WHERE phone = %s"
                print("Using phone query")
            
            print(f"Executing query: {query} with param: {login_field}")
            cursor.execute(query, (login_field,))
            user = cursor.fetchone()
            print(f"User found: {user}")
            
            if not user:
                print("No user found")
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
            # Verify password
            print("Verifying password...")
            if bcrypt.checkpw(data['pass'].encode('utf-8'), user['password'].encode('utf-8')):
                print("Password verified successfully")
                
                # Create custom session token instead of using Flask session
                is_admin = bool(user.get('is_admin', False))
                session_token = create_session_token(user['id'], user['name'], user['email'], is_admin)
                print(f"Custom session token created: {session_token}")
                
                response_data = {
                    'success': True,
                    'message': 'Login successful!',
                    'token': session_token,  # Send token to client
                    'user': {
                        'id': user['id'],
                        'name': user['name'],
                        'email': user['email'],
                        'phone': user['phone'],
                        'profile_pic': user.get('profile_pic'),
                        'is_admin': is_admin
                    }
                }
                print(f"Sending response: {response_data}")
                
                # Create response with proper session handling
                from flask import make_response
                response = make_response(jsonify(response_data))
                
                # Set custom session token cookie
                response.set_cookie('auth_token', 
                                   value=session_token,
                                   httponly=True,
                                   secure=False,
                                   samesite='Lax',
                                   path='/',
                                   domain=None,
                                   max_age=86400 # 24 hours
                )
                return response, 200
            else:
                print("Password verification failed")
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
                
        except Error as e:
            print(f"Database error during login: {e}")
            return jsonify({'success': False, 'message': 'Login failed'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("Database connection closed")
                
    except Exception as e:
        print(f"General error during login: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    # Clear Flask session
    session.clear()
    
    # Check for auth token in cookie or header
    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    
    # Also clear custom session token if provided
    if auth_token:
        delete_session_token(auth_token)
        print(f"Custom session token {auth_token} deleted")
    
    response = jsonify({'success': True, 'message': 'Logout successful'})
    response.delete_cookie('auth_token')
    return response, 200

@app.route('/api/debug-session', methods=['GET'])
def debug_session():
    """Debug endpoint to check session status"""
    return jsonify({
        'session_data': dict(session),
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name'),
        'session_keys': list(session.keys())
    })

@app.route('/api/debug-cookies', methods=['GET'])
def debug_cookies():
    """Debug endpoint to see all cookies and session data"""
    print("=== COOKIE DEBUG ===")
    print(f"All request cookies: {dict(request.cookies)}")
    print(f"Session data: {dict(session)}")
    print(f"Session keys: {list(session.keys())}")
    
    return jsonify({
        'cookies_received': dict(request.cookies),
        'session_data': dict(session),
        'session_keys': list(session.keys()),
        'has_session_cookie': 'session' in request.cookies
    }), 200

@app.route('/api/test-cookies', methods=['GET'])
def test_cookies():
    """Test endpoint to verify cookies are being sent"""
    print("=== COOKIE TEST REQUEST ===")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request cookies: {dict(request.cookies)}")
    print(f"Session data: {dict(session)}")
    
    return jsonify({
        'success': True,
        'cookies_received': dict(request.cookies),
        'session_data': dict(session),
        'headers': dict(request.headers)
    }), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated using custom token or Authorization header"""
    print("=== AUTH CHECK REQUEST ===")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request cookies: {dict(request.cookies)}")
    print(f"Session data: {dict(session)}")
    
    # Check for custom auth token cookie first
    auth_token = request.cookies.get('auth_token')
    print(f"Auth token from cookie: {auth_token}")
    
    # If no cookie, check Authorization header
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        print(f"Authorization header: {auth_header}")
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]  # Remove 'Bearer ' prefix
            print(f"Auth token from header: {auth_token}")
    
    if auth_token:
        # Validate custom session token
        token_data = validate_session_token(auth_token)
        print(f"Token validation result: {token_data}")
        
        if token_data:
            print("✅ User is authenticated via custom token")
            
            # Fetch full user details including profile_pic from database
            user_details = {
                'id': token_data['user_id'],
                'name': token_data['user_name'],
                'email': token_data['user_email']
            }
            
            try:
                config_users = DB_CONFIG.copy()
                config_users['database'] = DB_NAMES['users']
                connection = mysql.connector.connect(**config_users)
                if connection:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT name, email, phone, profile_pic, is_admin FROM users WHERE id = %s", (token_data['user_id'],))
                    db_user = cursor.fetchone()
                    if db_user:
                        user_details.update(db_user)
                        user_details['is_admin'] = bool(db_user.get('is_admin', False))
                    cursor.close()
                    connection.close()
            except Exception as e:
                print(f"Error fetching user details in check_auth: {e}")
            
            response = jsonify({
                'success': True,
                'authenticated': True,
                'user': user_details
            })
            return response, 200
        else:
            print("❌ Token is invalid or expired")
    
    print("❌ No valid auth token found")
    response = jsonify({
        'success': True,
        'authenticated': False
    })
    return response, 200

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile"""
    # Check for custom auth token cookie first
    auth_token = request.cookies.get('auth_token')
    
    # If no cookie, check Authorization header
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    if not auth_token:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Validate custom session token
    token_data = validate_session_token(auth_token)
    if not token_data:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Connect to users database
    config_users = DB_CONFIG.copy()
    config_users['database'] = DB_NAMES['users']
    
    connection = mysql.connector.connect(**config_users)
    if connection is None:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, name, email, phone, address, pincode, dob FROM users WHERE id = %s"
        cursor.execute(query, (token_data['user_id'],))
        user = cursor.fetchone()
        
        if user:
            return jsonify({'success': True, 'user': user}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
    except Error as e:
        print(f"Error fetching user profile: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch profile'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Found Items API Endpoints
@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """Simple test endpoint to verify connectivity"""
    print("=== TEST ENDPOINT CALLED ===")
    print(f"Method: {request.method}")
    print(f"Session: {dict(session)}")
    return jsonify({'success': True, 'message': 'Test endpoint working', 'method': request.method})

@app.route('/api/found-items', methods=['POST'])
def report_found_item():
    """Report a new found item using custom token"""
    print("=== FOUND ITEM REPORT ===")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request cookies: {dict(request.cookies)}")
    print(f"Session data: {dict(session)}")
    
    try:
        # Check for custom auth token cookie first
        auth_token = request.cookies.get('auth_token')
        print(f"Auth token from cookie: {auth_token}")
        
        # If no cookie, check Authorization header
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            print(f"Authorization header: {auth_header}")
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]  # Remove 'Bearer ' prefix
                print(f"Auth token from header: {auth_token}")
        
        if not auth_token:
            print("❌ No auth token found")
            return jsonify({'success': False, 'message': 'Please login to report found items'}), 401
        
        # Validate custom session token
        token_data = validate_session_token(auth_token)
        print(f"Token validation result: {token_data}")
        
        if not token_data:
            print("❌ Token is invalid or expired")
            return jsonify({'success': False, 'message': 'Please login to report found items'}), 401
        
        print(f"✅ User authenticated: {token_data['user_name']} ({token_data['user_id']})")
        
        # Check if file was uploaded
        if 'foundItemImage' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'}), 400
        
        file = request.files['foundItemImage']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type. Only JPG, JPEG, PNG, WEBP allowed'}), 400
        
        # Get form data
        item_name = request.form.get('foundItemName')
        description = request.form.get('foundItemDesc')
        location_found = request.form.get('foundItemLocation')
        date_found = request.form.get('foundItemDate')
        category = request.form.get('foundItemCategory')
        
        # Validate required fields
        if not all([item_name, description, location_found, date_found, category]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        try:
            file.save(file_path)
        except Exception as e:
            print(f"Error saving uploaded file: {e}")
            return jsonify({'success': False, 'message': f'Failed to save image: {e}'}), 500
        
        # Connect to found_items database
        config_found_items = DB_CONFIG.copy()
        config_found_items['database'] = DB_NAMES['found_items']
        
        connection = mysql.connector.connect(**config_found_items)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO found_items (item_name, description, location_found, date_found, category, image_path, reported_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (item_name, description, location_found, date_found, category, unique_filename, token_data['user_id']))
            
            connection.commit()
            print(f"Found item reported: {item_name} by user {token_data['user_id']}")
            
            response = jsonify({
                'success': True,
                'message': 'Found item reported successfully!',
                'item_id': cursor.lastrowid
            })
            return response, 201
            
        except Error as e:
            print(f"Error saving found item: {e}")
            # Clean up uploaded file if database save fails
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'message': f'Failed to save found item: {e}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Error reporting found item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/found-items', methods=['GET'])
def get_found_items():
    """Get all found items"""
    try:
        # Connect to found_items database
        config_found_items = DB_CONFIG.copy()
        config_found_items['database'] = DB_NAMES['found_items']
        
        connection = mysql.connector.connect(**config_found_items)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM found_items 
                WHERE status = 'available' 
                ORDER BY created_at DESC
            """)
            items = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'items': items
            }), 200
            
        except Error as e:
            print(f"Error fetching found items: {e}")
            return jsonify({'success': False, 'message': 'Failed to fetch found items'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Error in get_found_items: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/lost-items', methods=['POST'])
def report_lost_item():
    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    if not auth_token:
        return jsonify({'success': False, 'message': 'Please login to report lost items'}), 401

    token_data = validate_session_token(auth_token)
    if not token_data:
        return jsonify({'success': False, 'message': 'Please login to report lost items'}), 401

    data = request.get_json() or {}
    item_name = data.get('item_name')
    description = data.get('description')
    location_lost = data.get('location_lost')
    date_lost = data.get('date_lost')
    category = data.get('category')

    if not all([item_name, description, location_lost, date_lost, category]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    config_lost_items = DB_CONFIG.copy()
    config_lost_items['database'] = DB_NAMES['lost_items']

    connection = mysql.connector.connect(**config_lost_items)
    if connection is None:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO lost_items (item_name, description, location_lost, date_lost, category, reported_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (item_name, description, location_lost, date_lost, category, token_data['user_id']))
        connection.commit()

        response = jsonify({
            'success': True,
            'message': 'Lost item reported successfully!',
            'item_id': cursor.lastrowid
        })
        return response, 201
    except Error as e:
        print(f"Error saving lost item: {e}")
        return jsonify({'success': False, 'message': f'Failed to save lost item: {e}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/lost-items', methods=['GET'])
def get_lost_items():
    try:
        config_lost_items = DB_CONFIG.copy()
        config_lost_items['database'] = DB_NAMES['lost_items']

        connection = mysql.connector.connect(**config_lost_items)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM lost_items
                WHERE status = 'lost'
                ORDER BY created_at DESC
            """)
            items = cursor.fetchall()

            return jsonify({
                'success': True,
                'items': items
            }), 200
        except Error as e:
            print(f"Error fetching lost items: {e}")
            return jsonify({'success': False, 'message': 'Failed to fetch lost items'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    except Exception as e:
        print(f"Error in get_lost_items: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/found-items/<int:item_id>/claim', methods=['POST'])
def claim_found_item(item_id):
    """Claim a found item - move from found_items to claimed_items table"""
    # Check for custom auth token cookie first
    auth_token = request.cookies.get('auth_token')
    
    # If no cookie, check Authorization header
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    if not auth_token:
        return jsonify({'success': False, 'message': 'Please login to claim items'}), 401
    
    # Validate custom session token
    token_data = validate_session_token(auth_token)
    if not token_data:
        return jsonify({'success': False, 'message': 'Please login to claim items'}), 401
    
    try:
        connection = create_server_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get the found item details
            cursor.execute(f"SELECT * FROM {DB_NAMES['found_items']}.found_items WHERE id = %s AND status = 'available'", (item_id,))
            found_item = cursor.fetchone()
            
            if not found_item:
                return jsonify({'success': False, 'message': 'Item not available or already claimed'}), 400
            
            # Move item to claimed_items table
            cursor.execute(f"""
                INSERT INTO {DB_NAMES['claimed_items']}.claimed_items (
                    original_found_item_id, item_name, description, location_found, 
                    date_found, category, image_path, reported_by, claimed_by, date_claimed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                found_item['id'],
                found_item['item_name'],
                found_item['description'],
                found_item['location_found'],
                found_item['date_found'],
                found_item['category'],
                found_item['image_path'],
                found_item['reported_by'],
                token_data['user_id'],
                datetime.now().date()
            ))
            
            # Update found_items status to claimed
            cursor.execute(f"UPDATE {DB_NAMES['found_items']}.found_items SET status = 'claimed' WHERE id = %s", (item_id,))
            
            connection.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Item claimed successfully! Please contact the lost and found office to complete the claim process.'
            }), 200
                
        except Error as e:
            print(f"Error claiming item: {e}")
            connection.rollback()
            return jsonify({'success': False, 'message': 'Failed to claim item'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Error claiming item: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/predict-category', methods=['POST'])
def predict_category():
    """Predict category based on item description using ML"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        
        if not description:
            return jsonify({'success': False, 'message': 'Description is required'}), 400
            
        result = ml_system.predict_category(description)
        
        return jsonify({
            'success': True,
            'category': result['category'],
            'confidence': result['confidence']
        }), 200
        
    except Exception as e:
        print(f"Error predicting category: {e}")
        return jsonify({'success': False, 'message': 'Prediction failed'}), 500

# Advanced NLP Search with TF-IDF and Cosine Similarity
@app.route('/api/smart-search', methods=['POST'])
def smart_search():
    """Advanced search using TF-IDF and cosine similarity"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'message': 'Search query is required'}), 400
        
        # Get filters
        filters = {
            'category': data.get('category', ''),
            'location': data.get('location', ''),
            'date_filter': data.get('date_filter', ''),
            'min_match_score': int(data.get('min_match_score', 0))
        }
        
        config_found_items = DB_CONFIG.copy()
        config_found_items['database'] = DB_NAMES['found_items']
        config_lost_items = DB_CONFIG.copy()
        config_lost_items['database'] = DB_NAMES['lost_items']
        
        connection = mysql.connector.connect(**config_found_items)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        lost_connection = mysql.connector.connect(**config_lost_items)
        if lost_connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            lost_cursor = lost_connection.cursor(dictionary=True)
            
            # Fetch all available found items
            base_query = """
                SELECT * FROM found_items 
                WHERE status = 'available'
            """
            params = []
            
            if filters['category']:
                base_query += " AND category = %s"
                params.append(filters['category'])
            
            if filters['location']:
                base_query += " AND location_found LIKE %s"
                params.append(f"%{filters['location']}%")
            
            if filters['date_filter']:
                base_query += " AND date_found >= %s"
                params.append(filters['date_filter'])
            
            base_query += " ORDER BY created_at DESC"
            
            cursor.execute(base_query, params)
            found_items = cursor.fetchall()
            for item in found_items:
                item['item_type'] = 'found'
            
            # Fetch all lost items
            lost_query = """
                SELECT * FROM lost_items
                WHERE status = 'lost'
            """
            lost_params = []
            
            if filters['category']:
                lost_query += " AND category = %s"
                lost_params.append(filters['category'])
            
            if filters['location']:
                lost_query += " AND location_lost LIKE %s"
                lost_params.append(f"%{filters['location']}%")
            
            if filters['date_filter']:
                lost_query += " AND date_lost >= %s"
                lost_params.append(filters['date_filter'])
            
            lost_query += " ORDER BY created_at DESC"
            
            lost_cursor.execute(lost_query, lost_params)
            lost_items = lost_cursor.fetchall()
            for item in lost_items:
                item['item_type'] = 'lost'
            
            items = found_items + lost_items
            
            # Use ML system to find similar items
            processed_items = ml_system.search_similar_items(query, items, threshold=filters['min_match_score']/100.0)
            
            # Format dates for JSON response
            for item in processed_items:
                if isinstance(item.get('date_found'), (datetime, date)):
                    item['date_found'] = item['date_found'].strftime('%Y-%m-%d')
                if isinstance(item.get('date_lost'), (datetime, date)):
                    item['date_lost'] = item['date_lost'].strftime('%Y-%m-%d')
                if isinstance(item.get('created_at'), (datetime, date)):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'success': True,
                'items': processed_items,
                'total_results': len(processed_items),
                'query_processed': query
            }), 200
            
        except Error as e:
            print(f"Error in smart search: {e}")
            return jsonify({'success': False, 'message': 'Search failed'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
            if lost_connection.is_connected():
                lost_cursor.close()
                lost_connection.close()
                
    except Exception as e:
        print(f"Error in smart search: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# Removed manual TF-IDF functions as they are now handled by ml_model.py
# preprocess_text and stem_word are kept for search feedback system

def preprocess_text(text):
    """Preprocess text for feedback system"""
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Tokenize and remove stopwords
    words = text.split()
    
    # Simple stopwords list
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    
    # Remove stopwords and short words
    words = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Apply stemming (simple version)
    words = [stem_word(word) for word in words]
    
    return ' '.join(words)

def stem_word(word):
    """Simple stemming function"""
    # Common suffixes to remove
    suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'ness', 'ment', 'able', 'ible', 'ant', 'ent', 'ion', 'ou', 'ism', 'ate', 'iti', 'ous', 'ive', 'ize', 'ise']
    
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    
    return word

# Supervised Learning Functions
def record_search_feedback(user_query, item_id, relevance_score, user_id, interaction_type):
    """Record user interaction for supervised learning"""
    try:
        connection = create_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO search_feedback (user_query, item_id, relevance_score, user_id, interaction_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_query, item_id, relevance_score, user_id, interaction_type))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Update search weights based on feedback
        update_search_weights(user_query, item_id, relevance_score, interaction_type)
        return True
        
    except Error as e:
        print(f"Error recording search feedback: {e}")
        return False

def update_search_weights(user_query, item_id, relevance_score, interaction_type):
    """Update term weights based on user feedback"""
    try:
        connection = create_server_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor(dictionary=True)
        
        # Get item details
        cursor.execute(f"SELECT * FROM {DB_NAMES['found_items']}.found_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            cursor.close()
            connection.close()
            return False
        
        # Extract terms from query and item
        query_terms = set(preprocess_text(user_query).split())
        item_terms = set(preprocess_text(f"{item['item_name']} {item['description']}").split())
        
        # Update weights for matching terms
        for term in query_terms & item_terms:
            # Calculate new weight based on feedback
            weight_adjustment = 0.1 if interaction_type == 'claim' else (-0.05 if interaction_type == 'skip' else 0.02)
            
            cursor.execute(f"""
                INSERT INTO {DB_NAMES['main']}.search_weights (term, category, weight, usage_count, success_rate)
                VALUES (%s, %s, %s, 1, %s)
                ON DUPLICATE KEY UPDATE 
                weight = weight + %s,
                usage_count = usage_count + 1,
                success_rate = (success_rate * (usage_count - 1) + %s) / usage_count,
                last_updated = CURRENT_TIMESTAMP
            """, (term, item['category'], 1.0 + weight_adjustment, 1.0 if relevance_score > 3 else 0.5,
                  weight_adjustment, 1.0 if relevance_score > 3 else 0.5))
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"Error updating search weights: {e}")
        return False

# Removed get_learned_weights and calculate_enhanced_tfidf as they are no longer used

# Feedback endpoints for supervised learning
@app.route('/api/search-feedback', methods=['POST'])
def record_feedback():
    """Record user feedback for supervised learning"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        item_id = data.get('item_id')
        relevance_score = data.get('relevance_score', 3)  # 1-5 scale
        interaction_type = data.get('interaction_type', 'view')  # view, claim, skip
        
        if not user_query or not item_id:
            return jsonify({'success': False, 'message': 'Query and item ID are required'}), 400
        
        user_id = None
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        if auth_token:
            token_data = validate_session_token(auth_token)
            if token_data:
                user_id = token_data['user_id']
        
        # Record feedback
        success = record_search_feedback(user_query, item_id, relevance_score, user_id, interaction_type)
        
        if success:
            return jsonify({'success': True, 'message': 'Feedback recorded successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to record feedback'}), 500
            
    except Exception as e:
        print(f"Error recording feedback: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/search-analytics', methods=['GET'])
def get_search_analytics():
    """Get search analytics and learning insights"""
    try:
        connection = create_server_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get top performing terms
        cursor.execute(f"""
            SELECT term, category, weight, usage_count, success_rate 
            FROM {DB_NAMES['main']}.search_weights 
            WHERE usage_count > 2 
            ORDER BY weight DESC 
            LIMIT 20
        """)
        top_terms = cursor.fetchall()
        
        # Get recent feedback
        cursor.execute(f"""
            SELECT sf.*, fi.item_name, u.name as user_name
            FROM {DB_NAMES['main']}.search_feedback sf
            LEFT JOIN {DB_NAMES['found_items']}.found_items fi ON sf.item_id = fi.id
            LEFT JOIN {DB_NAMES['users']}.users u ON sf.user_id = u.id
            ORDER BY sf.created_at DESC
            LIMIT 10
        """)
        recent_feedback = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'top_terms': top_terms,
            'recent_feedback': recent_feedback
        }), 200
        
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/my-found-items', methods=['GET'])
def get_my_found_items():
    """Get items found by the current user along with any claim requests"""
    # Verify authentication
    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    
    if not auth_token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get found items
        config_found = DB_CONFIG.copy()
        config_found['database'] = DB_NAMES['found_items']
        
        connection_found = mysql.connector.connect(**config_found)
        if connection_found is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor_found = connection_found.cursor(dictionary=True)
            # Fetch items reported by this user
            cursor_found.execute("""
                SELECT * FROM found_items 
                WHERE reported_by = %s AND status = 'available'
                ORDER BY created_at DESC
            """, (user_id,))
            
            found_items = cursor_found.fetchall()
            
            # For each item, check for claim requests
            config_claimed = DB_CONFIG.copy()
            config_claimed['database'] = DB_NAMES['claimed_items']
            connection_claimed = mysql.connector.connect(**config_claimed)
            cursor_claimed = connection_claimed.cursor(dictionary=True)
            
            for item in found_items:
                # Get claim requests linked to this item
                cursor_claimed.execute("""
                    SELECT * FROM claim_requests 
                    WHERE found_item_id = %s
                """, (item['id'],))
                claims = cursor_claimed.fetchall()
                item['claims'] = claims
                
                # Format dates
                if item.get('date_found'):
                    item['date_found'] = item['date_found'].strftime('%Y-%m-%d')
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                for claim in claims:
                    if claim.get('created_at'):
                        claim['created_at'] = claim['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({'success': True, 'items': found_items})
            
        except Error as e:
            print(f"Error fetching my found items: {e}")
            return jsonify({'success': False, 'message': 'Failed to fetch items'}), 500
        finally:
            if connection_found.is_connected():
                cursor_found.close()
                connection_found.close()
            if 'connection_claimed' in locals() and connection_claimed.is_connected():
                cursor_claimed.close()
                connection_claimed.close()
                
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error in get_my_found_items: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/my-lost-items', methods=['GET'])
def get_my_lost_items():
    """Get items lost by the current user along with any found requests"""
    # Verify authentication
    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    
    if not auth_token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get lost items
        config_lost = DB_CONFIG.copy()
        config_lost['database'] = DB_NAMES['lost_items']
        
        connection_lost = mysql.connector.connect(**config_lost)
        if connection_lost is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor_lost = connection_lost.cursor(dictionary=True)
            # Fetch items reported by this user
            cursor_lost.execute("""
                SELECT * FROM lost_items 
                WHERE reported_by = %s AND status = 'lost'
                ORDER BY created_at DESC
            """, (user_id,))
            
            lost_items = cursor_lost.fetchall()
            
            # For each item, check for found requests
            config_claimed = DB_CONFIG.copy()
            config_claimed['database'] = DB_NAMES['claimed_items']
            connection_claimed = mysql.connector.connect(**config_claimed)
            cursor_claimed = connection_claimed.cursor(dictionary=True)
            
            for item in lost_items:
                # Get found requests linked to this lost item
                cursor_claimed.execute("""
                    SELECT * FROM found_requests 
                    WHERE lost_item_id = %s
                """, (item['id'],))
                requests = cursor_claimed.fetchall()
                item['found_requests'] = requests
                
                # Format dates
                if item.get('date_lost'):
                    item['date_lost'] = item['date_lost'].strftime('%Y-%m-%d')
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                for req in requests:
                    if req.get('created_at'):
                        req['created_at'] = req['created_at'].strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({'success': True, 'items': lost_items})
            
        except Error as e:
            print(f"Error fetching my lost items: {e}")
            return jsonify({'success': False, 'message': 'Failed to fetch items'}), 500
        finally:
            if connection_lost.is_connected():
                cursor_lost.close()
                connection_lost.close()
            if 'connection_claimed' in locals() and connection_claimed.is_connected():
                cursor_claimed.close()
                connection_claimed.close()
                
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error in get_my_lost_items: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/lost-items/<int:item_id>/found-request', methods=['POST'])
def submit_found_request(item_id):
    """Submit a found request specifically for a lost item"""
    try:
        # Check for auth token
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        
        if not auth_token:
            return jsonify({'success': False, 'message': 'Authentication required to report found items'}), 401
            
        # Validate session token
        token_data = validate_session_token(auth_token)
        if not token_data:
            return jsonify({'success': False, 'message': 'Invalid session. Please login again.'}), 401
        
        data = request.get_json()
        
        # Validate description
        if not data.get('description'):
            return jsonify({'success': False, 'message': 'Description is required'}), 400
        
        # Connect to lost_items database to get item details
        config_lost = DB_CONFIG.copy()
        config_lost['database'] = DB_NAMES['lost_items']
        connection_lost = mysql.connector.connect(**config_lost)
        
        item_name = 'Lost Item'
        
        if connection_lost:
            try:
                cursor_lost = connection_lost.cursor(dictionary=True)
                cursor_lost.execute("SELECT item_name FROM lost_items WHERE id = %s", (item_id,))
                lost_item = cursor_lost.fetchone()
                if lost_item:
                    item_name = lost_item['item_name']
            finally:
                if connection_lost.is_connected():
                    cursor_lost.close()
                    connection_lost.close()

        # Connect to claimed_items database (where found_requests table is)
        config_claimed = DB_CONFIG.copy()
        config_claimed['database'] = DB_NAMES['claimed_items']
        
        connection = mysql.connector.connect(**config_claimed)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor()
            
            # Use authenticated user details
            cursor.execute("""
                INSERT INTO found_requests (finder_name, finder_email, item_name, description, location_found, lost_item_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                token_data['user_name'],
                token_data['user_email'],
                item_name,
                data['description'],
                data.get('location_found', 'Unknown'),
                item_id
            ))
            
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Found request submitted successfully! The owner will be notified.'
            }), 201
            
        except Error as e:
            print(f"Error submitting found request: {e}")
            return jsonify({'success': False, 'message': 'Failed to submit found request'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Error in submit_found_request: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/lost-items/<int:item_id>', methods=['DELETE'])
def delete_lost_item(item_id):
    """Delete a reported lost item (and resolve associated found requests)"""
    # Verify authentication
    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    
    if not auth_token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Connect to lost_items database
        config_lost = DB_CONFIG.copy()
        config_lost['database'] = DB_NAMES['lost_items']
        
        connection_lost = mysql.connector.connect(**config_lost)
        if connection_lost is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor_lost = connection_lost.cursor()
            
            # Verify ownership
            cursor_lost.execute("SELECT reported_by FROM lost_items WHERE id = %s", (item_id,))
            result = cursor_lost.fetchone()
            
            if not result:
                return jsonify({'success': False, 'message': 'Item not found'}), 404
                
            if result[0] != user_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Delete item
            cursor_lost.execute("DELETE FROM lost_items WHERE id = %s", (item_id,))
            connection_lost.commit()
            
            # Clean up associated found requests
            try:
                config_claimed = DB_CONFIG.copy()
                config_claimed['database'] = DB_NAMES['claimed_items']
                connection_claimed = mysql.connector.connect(**config_claimed)
                if connection_claimed:
                    cursor_claimed = connection_claimed.cursor()
                    cursor_claimed.execute("DELETE FROM found_requests WHERE lost_item_id = %s", (item_id,))
                    connection_claimed.commit()
                    cursor_claimed.close()
                    connection_claimed.close()
            except Exception as e:
                print(f"Error cleaning up found requests: {e}")
                # Don't fail the main deletion
            
            return jsonify({'success': True, 'message': 'Item deleted successfully'}), 200
            
        except Error as e:
            print(f"Error deleting lost item: {e}")
            return jsonify({'success': False, 'message': 'Failed to delete item'}), 500
        finally:
            if connection_lost.is_connected():
                cursor_lost.close()
                connection_lost.close()
                
    except Exception as e:
        print(f"Error in delete_lost_item: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/found-items/<int:item_id>/claim-request', methods=['POST'])
def submit_specific_claim_request(item_id):
    """Submit a claim request specifically for a found item"""
    try:
        # Check for auth token
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        
        if not auth_token:
            return jsonify({'success': False, 'message': 'Authentication required to claim items'}), 401
            
        # Validate session token
        token_data = validate_session_token(auth_token)
        if not token_data:
            return jsonify({'success': False, 'message': 'Invalid session. Please login again.'}), 401
            
        data = request.get_json()
        
        # Validate description
        if not data.get('description'):
            return jsonify({'success': False, 'message': 'Description/Proof is required'}), 400
        
        # Connect to found_items database to get item details
        config_found = DB_CONFIG.copy()
        config_found['database'] = DB_NAMES['found_items']
        connection_found = mysql.connector.connect(**config_found)
        
        item_name = 'Linked Claim'
        location = 'Unknown'
        
        if connection_found:
            try:
                cursor_found = connection_found.cursor(dictionary=True)
                cursor_found.execute("SELECT item_name, location_found FROM found_items WHERE id = %s", (item_id,))
                found_item = cursor_found.fetchone()
                if found_item:
                    item_name = found_item['item_name']
                    location = found_item['location_found']
            finally:
                if connection_found.is_connected():
                    cursor_found.close()
                    connection_found.close()

        # Connect to claimed_items database
        config_claimed = DB_CONFIG.copy()
        config_claimed['database'] = DB_NAMES['claimed_items']
        
        connection = mysql.connector.connect(**config_claimed)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor()
            
            # Use authenticated user details
            cursor.execute("""
                INSERT INTO claim_requests (claimant_name, claimant_email, item_name, description, location_lost, found_item_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                token_data['user_name'],
                token_data['user_email'],
                item_name,
                data['description'],
                location,
                item_id
            ))
            
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Claim request submitted successfully! The reporter will be notified.'
            }), 201
            
        except Error as e:
            print(f"Error submitting linked claim request: {e}")
            return jsonify({'success': False, 'message': 'Failed to submit claim request'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Error in submit_specific_claim_request: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/found-items/<int:item_id>', methods=['DELETE'])
def delete_found_item(item_id):
    """Delete a reported found item (and resolve associated claims)"""
    # Verify authentication
    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
    
    if not auth_token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
    try:
        payload = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Connect to found_items database
        config_found = DB_CONFIG.copy()
        config_found['database'] = DB_NAMES['found_items']
        
        connection_found = mysql.connector.connect(**config_found)
        if connection_found is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor_found = connection_found.cursor()
            
            # Verify ownership
            cursor_found.execute("SELECT reported_by FROM found_items WHERE id = %s", (item_id,))
            result = cursor_found.fetchone()
            
            if not result:
                return jsonify({'success': False, 'message': 'Item not found'}), 404
                
            if result[0] != user_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Delete item
            cursor_found.execute("DELETE FROM found_items WHERE id = %s", (item_id,))
            connection_found.commit()
            
            # Clean up associated claims
            try:
                config_claimed = DB_CONFIG.copy()
                config_claimed['database'] = DB_NAMES['claimed_items']
                connection_claimed = mysql.connector.connect(**config_claimed)
                if connection_claimed:
                    cursor_claimed = connection_claimed.cursor()
                    cursor_claimed.execute("DELETE FROM claim_requests WHERE found_item_id = %s", (item_id,))
                    connection_claimed.commit()
                    cursor_claimed.close()
                    connection_claimed.close()
            except Exception as e:
                print(f"Error cleaning up claims: {e}")
                # Don't fail the main deletion if claim cleanup fails
            
            return jsonify({'success': True, 'message': 'Item deleted successfully'}), 200
            
        except Error as e:
            print(f"Error deleting found item: {e}")
            return jsonify({'success': False, 'message': 'Failed to delete item'}), 500
        finally:
            if connection_found.is_connected():
                cursor_found.close()
                connection_found.close()
                
    except Exception as e:
        print(f"Error in delete_found_item: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/claim-request', methods=['POST'])
def submit_claim_request():
    """Submit a general claim request/inquiry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['claimant_name', 'claimant_email', 'item_name', 'description', 'location_lost']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Connect to claimed_items database
        config_claimed = DB_CONFIG.copy()
        config_claimed['database'] = DB_NAMES['claimed_items']
        
        connection = mysql.connector.connect(**config_claimed)
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO claim_requests (claimant_name, claimant_email, item_name, description, location_lost)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['claimant_name'],
                data['claimant_email'],
                data['item_name'],
                data['description'],
                data['location_lost']
            ))
            
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': 'Claim request submitted successfully! We will contact you if we find a match.'
            }), 201
            
        except Error as e:
            print(f"Error submitting claim request: {e}")
            return jsonify({'success': False, 'message': 'Failed to submit claim request'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    except Exception as e:
        print(f"Error in submit_claim_request: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# Contact and Feedback Endpoints

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        user_name = data.get('userName')
        user_email = data.get('userEmail')
        message = data.get('userMessage')
        
        if not all([user_name, user_email, message]):
             return jsonify({'success': False, 'message': 'All fields are required'}), 400
             
        # Use main DB for contact_messages
        conn = create_db_connection()
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
             
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO contact_messages (user_name, user_email, message)
                VALUES (%s, %s, %s)
            """, (user_name, user_email, message))
            conn.commit()
            return jsonify({'success': True, 'message': 'Message sent successfully'}), 200
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
    except Exception as e:
        print(f"Error submitting contact form: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        comments = data.get('comments')
        
        # Use main DB for feedbacks
        conn = create_db_connection()
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
             
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedbacks (name, email, phone, comments)
                VALUES (%s, %s, %s, %s)
            """, (name, email, phone, comments))
            conn.commit()
            return jsonify({'success': True, 'message': 'Feedback submitted successfully'}), 200
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# Admin Endpoints

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        
        if not auth_token:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
        token_data = validate_session_token(auth_token)
        if not token_data:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
            
        # Check admin status
        if not token_data.get('is_admin'):
             return jsonify({'success': False, 'message': 'Admin access required'}), 403
             
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/history', methods=['GET'])
@admin_required
def get_admin_history():
    try:
        conn = create_db_connection()
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            # Join with users table to get admin name
            query = f"""
                SELECT h.*, u.name as admin_name
                FROM {DB_NAMES['main']}.admin_history h
                LEFT JOIN {DB_NAMES['users']}.users u ON h.admin_id = u.id
                ORDER BY h.created_at DESC
                LIMIT 100
            """
            cursor.execute(query)
            history = cursor.fetchall()
            
            # Format dates
            for item in history:
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return jsonify({'success': True, 'history': history}), 200
        finally:
             if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def log_admin_action(action_type, item_type, item_id, details, admin_id):
    """Log admin action to history table"""
    try:
        conn = create_db_connection()
        if not conn:
            print("Failed to connect to DB for logging")
            return False
            
        try:
            cursor = conn.cursor()
            
            # Convert details to JSON string if it's a dict/list
            if isinstance(details, (dict, list)):
                details_str = json.dumps(details, default=str)
            else:
                details_str = str(details)
                
            cursor.execute(f"""
                INSERT INTO {DB_NAMES['main']}.admin_history 
                (action_type, item_type, item_id, details, admin_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (action_type, item_type, item_id, details_str, admin_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging admin action: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        print(f"Error in log_admin_action: {e}")
        return False

@app.route('/api/admin/feedbacks', methods=['GET'])
@admin_required
def get_feedbacks():
    try:
        conn = create_db_connection()
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM feedbacks ORDER BY created_at DESC")
            feedbacks = cursor.fetchall()
            return jsonify({'success': True, 'feedbacks': feedbacks}), 200
        finally:
             if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/contact-messages', methods=['GET'])
@admin_required
def get_contact_messages():
    try:
        conn = create_db_connection()
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
            messages = cursor.fetchall()
            return jsonify({'success': True, 'messages': messages}), 200
        finally:
             if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/lost-items', methods=['GET'])
@admin_required
def get_admin_lost_items():
    try:
        config_lost = DB_CONFIG.copy()
        config_lost['database'] = DB_NAMES['lost_items']
        
        conn = mysql.connector.connect(**config_lost)
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            # Join with users table to get reporter name
            query = f"""
                SELECT l.*, u.name as reported_by_name, u.email as reported_by_email 
                FROM {DB_NAMES['lost_items']}.lost_items l 
                LEFT JOIN {DB_NAMES['users']}.users u ON l.reported_by = u.id 
                ORDER BY l.created_at DESC
            """
            cursor.execute(query)
            items = cursor.fetchall()
            
            # Formatting dates
            for item in items:
                if item.get('date_lost'):
                    item['date_lost'] = item['date_lost'].strftime('%Y-%m-%d')
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return jsonify({'success': True, 'items': items}), 200
        finally:
             if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/found-items', methods=['GET'])
@admin_required
def get_admin_found_items():
    try:
        config_found = DB_CONFIG.copy()
        config_found['database'] = DB_NAMES['found_items']
        
        conn = mysql.connector.connect(**config_found)
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            # Join with users table to get reporter name
            query = f"""
                SELECT f.*, u.name as reported_by_name, u.email as reported_by_email
                FROM {DB_NAMES['found_items']}.found_items f
                LEFT JOIN {DB_NAMES['users']}.users u ON f.reported_by = u.id
                ORDER BY f.created_at DESC
            """
            cursor.execute(query)
            items = cursor.fetchall()
            
            # Formatting dates
            for item in items:
                if item.get('date_found'):
                    item['date_found'] = item['date_found'].strftime('%Y-%m-%d')
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return jsonify({'success': True, 'items': items}), 200
        finally:
             if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/claims', methods=['GET'])
@admin_required
def get_admin_claims():
    try:
        config_claimed = DB_CONFIG.copy()
        config_claimed['database'] = DB_NAMES['claimed_items']
        
        conn = mysql.connector.connect(**config_claimed)
        if not conn:
             return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Fetch from claimed_items table (Verified/processed claims)
            # JOIN with users table to get names
            query_claims = f"""
                SELECT c.*, 
                       u1.name as claimed_by_name, u1.email as claimed_by_email,
                       u2.name as reported_by_name, u2.email as reported_by_email
                FROM {DB_NAMES['claimed_items']}.claimed_items c
                LEFT JOIN {DB_NAMES['users']}.users u1 ON c.claimed_by = u1.id
                LEFT JOIN {DB_NAMES['users']}.users u2 ON c.reported_by = u2.id
                ORDER BY c.created_at DESC
            """
            cursor.execute(query_claims)
            claims = cursor.fetchall()
            
            # Fetch from found_requests (Reports of finding a lost item)
            cursor.execute("SELECT * FROM found_requests ORDER BY created_at DESC")
            found_requests = cursor.fetchall()
            
            # Fetch from claim_requests (Requests to claim a found item)
            cursor.execute("SELECT * FROM claim_requests ORDER BY created_at DESC")
            claim_requests = cursor.fetchall()
            
            # Formatting dates
            for item in claims:
                if item.get('date_found'):
                    item['date_found'] = item['date_found'].strftime('%Y-%m-%d')
                if item.get('date_claimed'):
                    item['date_claimed'] = item['date_claimed'].strftime('%Y-%m-%d')
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            for item in found_requests:
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            for item in claim_requests:
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'success': True, 
                'claims': claims, 
                'found_requests': found_requests,
                'claim_requests': claim_requests
            }), 200
        finally:
             if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# DELETE Endpoints

@app.route('/api/admin/lost-items/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_lost_item(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['lost_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM lost_items WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'lost_item', id, item, admin_id)
            cursor.execute("DELETE FROM lost_items WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Lost item deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/found-items/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_found_item(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['found_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM found_items WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'found_item', id, item, admin_id)
            cursor.execute("DELETE FROM found_items WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Found item deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/claims/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_claim(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['claimed_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM claimed_items WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'claim', id, item, admin_id)
            cursor.execute("DELETE FROM claimed_items WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Claim deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/claims/<int:id>/verify', methods=['PUT'])
@admin_required
def admin_verify_claim(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['claimed_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM claimed_items WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('APPROVE', 'claim', id, item, admin_id)
            cursor.execute("UPDATE claimed_items SET verification_status = 'verified' WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Claim verified successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/claims/<int:id>/reject', methods=['PUT'])
@admin_required
def admin_reject_claim(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['claimed_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM claimed_items WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('REJECT', 'claim', id, item, admin_id)
            cursor.execute("UPDATE claimed_items SET verification_status = 'rejected' WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Claim rejected successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/found-requests/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_found_request(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['claimed_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM found_requests WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'found_request', id, item, admin_id)
            cursor.execute("DELETE FROM found_requests WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Found request deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/claim-requests/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_claim_request(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['claimed_items']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM claim_requests WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'claim_request', id, item, admin_id)
            cursor.execute("DELETE FROM claim_requests WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Claim request deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/feedbacks/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_feedback(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['main']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM feedbacks WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'feedback', id, item, admin_id)
            cursor.execute("DELETE FROM feedbacks WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Feedback deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/contact-messages/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_contact_message(id):
    try:
        # Get admin ID
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        token_data = validate_session_token(auth_token)
        admin_id = token_data['user_id']

        config = DB_CONFIG.copy()
        config['database'] = DB_NAMES['main']
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Get item details
        cursor.execute("SELECT * FROM contact_messages WHERE id = %s", (id,))
        item = cursor.fetchone()
        
        if item:
            log_admin_action('DELETE', 'contact_message', id, item, admin_id)
            cursor.execute("DELETE FROM contact_messages WHERE id = %s", (id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Message deleted successfully'}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    if init_database():
        print("Starting Flask server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to initialize database. Exiting.")
