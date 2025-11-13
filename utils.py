"""
Utility helpers: default admin creation and password hashing.
"""
import os
from models import db, User
import bcrypt

def create_default_admin():
    """
    Create a default admin user if no users exist.
    Credentials taken from env: DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD.
    """
    if User.query.first():
        return
    username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    # hash password with bcrypt
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    user = User(username=username, password_hash=pw_hash, role='owner')
    db.session.add(user)
    db.session.commit()
    print(f"Created default admin user: {username} (please change password in production)")
