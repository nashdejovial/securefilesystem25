
# 🔐 Secure File Sharing System

A secure, web-based file sharing platform built with Flask, PostgreSQL, and SQLAlchemy ORM. It allows users to register, verify their email, and safely upload, download, and manage encrypted files. The system enforces user authentication, email verification, and access control to ensure file confidentiality and privacy.

---

## 📌 Features

- ✅ User Registration & Login
- ✅ Email Verification before login
- ✅ File Upload with AES Encryption
- ✅ Secure File Download with Decryption
- ✅ User-Specific File Access Control
- ✅ Dashboard for File Management
- ✅ Database Integration using SQLAlchemy ORM

---

## 🛠 Tech Stack

| Layer       | Technology                     |
|-------------|--------------------------------|
| Backend     | Flask (Python)                 |
| Frontend    | HTML + Jinja2 Templates        |
| Database    | PostgreSQL + SQLAlchemy ORM    |
| Encryption  | Python `cryptography` library  |
| Email       | Flask-Mail                     |

---

## 🗂️ Project Structure

```
sproject_root/
│
├── run.py                  # Entry point to start the Flask app; initializes extensions and registers routes
├── config.py               # Configuration for Flask, database URI, JWT, and mail server
├── requirements.txt        # Python dependencies required for the project
│
├── extensions.py           # Initializes extensions like SQLAlchemy, JWT, Bcrypt, and Mail
│
├── models/                 # ORM models using SQLAlchemy
│   ├── __init__.py         # Imports and initializes all models
│   ├── user.py             # User model with roles, authentication, and password hashing
│   ├── file.py             # File model to store file metadata
│   ├── file_access.py      # FileAccess model to control who can access which files
│
├── routes/                 # Route handlers for different endpoints
│   ├── __init__.py         # Initializes route blueprints
│   ├── auth_routes.py      # Routes for login, registration, email verification
│   ├── user_routes.py      # Routes for user profile and account management
│   ├── file_routes.py      # Routes for file upload, download, sharing
│
├── utils/                  # Utility functions for encryption and emailing
│   ├── __init__.py         # Utility module initializer
│   ├── crypto.py           # AES encryption and decryption logic
│   └── email.py            # Email sending functions for verification and reset

```

---

## 🚀 Getting Started


### 2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Set up your environment variables (or edit in `__init__.py`):
```python
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 587
MAIL_USERNAME = 'your-email@example.com'
MAIL_PASSWORD = 'your-password'
MAIL_DEFAULT_SENDER = 'your-email@example.com'
```

### 5. Initialize the database:
```python
from app import create_app, db
app = create_app()
app.app_context().push()
db.create_all()
```

### 6. Run the application:
```bash
python run.py
```

Then visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## Security Notes

- Passwords are hashed using a secure hash (Werkzeug).
- Files are encrypted using AES before being stored.
- Email verification is required before login.
- Access is restricted to only the owner's files.
- role base access
- input validation

---

## 📬 Future Improvements

- Password reset via email
- Admin dashboard
- File sharing between users
- Expiring download links

---

