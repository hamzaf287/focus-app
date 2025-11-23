"""
Authentication Routes
Handles user registration, login, and logout
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from functools import wraps

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Models will be injected via init_routes function
user_model = None


def init_routes(db):
    """Initialize routes with database models"""
    global user_model
    from models.user_model import User
    user_model = User(db)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({"error": "Authentication required"}), 401

            user = user_model.find_by_id(session['user_id'])
            if not user or user['role'] != role:
                return jsonify({"error": "Unauthorized access"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user

    Expected JSON:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "role": "student"  # or "teacher" or "admin"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'email', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        name = data['name']
        email = data['email']
        password = data['password']
        role = data['role']

        # Validate role
        if role not in ['student', 'teacher', 'admin']:
            return jsonify({"error": "Invalid role. Must be 'student', 'teacher', or 'admin'"}), 400

        # Validate email format (basic check)
        if '@' not in email:
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password length
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Create user
        user = user_model.create_user(name, email, password, role)

        if not user:
            return jsonify({"error": "Email already registered"}), 409

        # Prepare response
        response_data = {
            "message": "User registered successfully",
            "user": {
                "id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "approved": user['approved']
            }
        }

        # Add notice for teachers
        if role == 'teacher' and not user['approved']:
            response_data['message'] += ". Waiting for admin approval."

        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user

    Expected JSON:
    {
        "email": "john@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password required"}), 400

        email = data['email']
        password = data['password']

        # Verify credentials
        user = user_model.verify_password(email, password)

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        # Create session (teachers can login even if not approved)
        session['user_id'] = str(user['_id'])
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        session.permanent = True

        return jsonify({
            "message": "Login successful",
            "user": {
                "id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "role": user['role']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Logout user and clear session"""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user information"""
    try:
        user = user_model.find_by_id(session['user_id'])

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "user": {
                "id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "approved": user['approved'],
                "enrolled_courses": [str(cid) for cid in user.get('enrolled_courses', [])] if user['role'] == 'student' else None,
                "teaching_course": str(user['teaching_course']) if user.get('teaching_course') else None
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch user: {str(e)}"}), 500


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "user_id": session['user_id'],
            "user_role": session.get('user_role')
        }), 200
    else:
        return jsonify({"authenticated": False}), 200
