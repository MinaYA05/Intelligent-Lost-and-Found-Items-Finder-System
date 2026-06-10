# Lost and Found Items Finder System - Backend Setup

This document provides instructions for setting up the Python Flask backend with MySQL database for the Lost and Found system.

## Prerequisites

1. **Python 3.7+** installed on your system
2. **MySQL Server** installed and running
3. **pip** (Python package installer)

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

1. Create a `.env` file in the root directory (you can copy the example below).
2. Add your database credentials and other configuration:

```ini
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production

# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME_MAIN=lostandfound_db

# Server Configuration
PORT=5000
ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5500

# File Uploads
UPLOAD_FOLDER=founditems
MAX_CONTENT_LENGTH=16777216
```

### 3. MySQL Database Setup

1. Start your MySQL server.
2. The application will use the credentials from your `.env` file.
3. Run the setup script to initialize databases:
   ```bash
   python setup_database.py
   ```

### 4. Run the Backend Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication Endpoints

#### POST /api/register
Register a new user account.

**Request Body:**
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "phonenum": "1234567890",
    "address": "123 Main St",
    "pincode": "123456",
    "dob": "1990-01-01",
    "pass": "password123",
    "cpass": "password123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Registration successful! Please login.",
    "user_id": 1
}
```

#### POST /api/login
Authenticate user and create session.

**Request Body:**
```json
{
    "email_mob": "john@example.com",  // Can be email or phone
    "pass": "password123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful!",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890"
    }
}
```

#### POST /api/logout
Logout user and clear session.

**Response:**
```json
{
    "success": true,
    "message": "Logout successful"
}
```

#### GET /api/check-auth
Check if user is authenticated.

**Response:**
```json
{
    "success": true,
    "authenticated": true,
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
    }
}
```

#### GET /api/user/profile
Get user profile information (requires authentication).

**Response:**
```json
{
    "success": true,
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "address": "123 Main St",
        "pincode": "123456",
        "dob": "1990-01-01",
        "profile_picture": null
    }
}
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | INT AUTO_INCREMENT | Primary key |
| name | VARCHAR(255) | User's full name |
| email | VARCHAR(255) UNIQUE | User's email address |
| phone | VARCHAR(20) | User's phone number |
| address | TEXT | User's address |
| pincode | VARCHAR(10) | Postal code |
| dob | DATE | Date of birth |
| password | VARCHAR(255) | Hashed password |
| profile_picture | VARCHAR(255) | Profile picture filename |
| created_at | TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | Last update time |

## Security Features

- Password hashing using bcrypt
- Session-based authentication
- Input validation for email and phone formats
- SQL injection prevention using parameterized queries
- CORS enabled for cross-origin requests

## Frontend Integration

The frontend JavaScript (`script.js`) is already configured to communicate with the backend API. The following features are implemented:

- Login form submission
- Registration form submission
- Authentication status checking
- UI updates based on login state
- Logout functionality

## Testing the System

1. Start the backend server: `python app.py`
2. Open `index.html` in your browser
3. Test registration by clicking "Register" and filling the form
4. Test login with the registered credentials
5. Verify the UI updates to show the logged-in user

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure MySQL server is running
   - Check database credentials in `app.py`
   - Verify MySQL user has necessary permissions

2. **CORS Errors**
   - The backend includes CORS configuration
   - Ensure the backend is running on port 5000

3. **Registration Fails**
   - Check if email or phone already exists
   - Verify all required fields are filled
   - Ensure passwords match

4. **Login Fails**
   - Verify correct email/phone and password
   - Check if user is registered in database

## Development Notes

- The backend uses Flask with Flask-CORS for API development
- MySQL connector for database operations
- bcrypt for secure password hashing
- Session management for user authentication
- Error handling and logging for debugging

## Production Deployment

For production deployment:

1. Change the Flask secret key
2. Use environment variables for database credentials
3. Implement proper logging
4. Add rate limiting for API endpoints
5. Use HTTPS for secure communication
6. Consider using a production WSGI server like Gunicorn
