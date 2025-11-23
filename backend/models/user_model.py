"""
User Model
Handles user data operations for students, teachers, and admins
"""

from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User:
    """User model for authentication and profile management"""

    def __init__(self, db):
        """Initialize with database connection"""
        self.collection = db.users

    def create_user(self, name, email, password, role):
        """
        Create a new user

        Args:
            name (str): User's full name
            email (str): User's email address
            password (str): Plain text password (will be hashed)
            role (str): User role - 'student', 'teacher', or 'admin'

        Returns:
            dict: Created user document or None if email exists
        """
        # Check if user already exists
        if self.collection.find_one({"email": email}):
            return None

        # Hash password
        password_hash = generate_password_hash(password)

        # Create user document
        user_doc = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "approved": True if role in ['student', 'admin'] else False,  # Teachers need approval
            "enrolled_courses": [] if role == 'student' else None,
            "teaching_course": None if role == 'teacher' else None,
            "created_at": datetime.utcnow()
        }

        # Insert into database
        result = self.collection.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id

        return user_doc

    def find_by_email(self, email):
        """
        Find user by email

        Args:
            email (str): User's email address

        Returns:
            dict: User document or None
        """
        return self.collection.find_one({"email": email})

    def find_by_id(self, user_id):
        """
        Find user by ID

        Args:
            user_id (str or ObjectId): User's ID

        Returns:
            dict: User document or None
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return self.collection.find_one({"_id": user_id})

    def verify_password(self, email, password):
        """
        Verify user password

        Args:
            email (str): User's email
            password (str): Plain text password to verify

        Returns:
            dict: User document if password is correct, None otherwise
        """
        user = self.find_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    def update_approval_status(self, user_id, approved):
        """
        Update teacher approval status (admin function)

        Args:
            user_id (str or ObjectId): User's ID
            approved (bool): Approval status

        Returns:
            bool: True if updated successfully
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": {"approved": approved}}
        )
        return result.modified_count > 0

    def assign_course_to_teacher(self, user_id, course_id):
        """
        Assign a course to a teacher

        Args:
            user_id (str or ObjectId): Teacher's ID
            course_id (str or ObjectId): Course ID

        Returns:
            bool: True if assigned successfully
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        result = self.collection.update_one(
            {"_id": user_id, "role": "teacher"},
            {"$set": {"teaching_course": course_id}}
        )
        return result.modified_count > 0

    def enroll_student_in_course(self, user_id, course_id):
        """
        Enroll a student in a course

        Args:
            user_id (str or ObjectId): Student's ID
            course_id (str or ObjectId): Course ID

        Returns:
            bool: True if enrolled successfully
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        result = self.collection.update_one(
            {"_id": user_id, "role": "student"},
            {"$addToSet": {"enrolled_courses": course_id}}
        )
        return result.modified_count > 0

    def get_unapproved_teachers(self):
        """
        Get all unapproved teachers (admin function)

        Returns:
            list: List of unapproved teacher documents
        """
        return list(self.collection.find({"role": "teacher", "approved": False}))

    def get_approved_teachers(self):
        """
        Get all approved teachers (admin function)

        Returns:
            list: List of approved teacher documents
        """
        return list(self.collection.find({
            "role": "teacher",
            "approved": True
        }).sort("name", 1))

    def get_all_students(self):
        """
        Get all students

        Returns:
            list: List of student documents
        """
        return list(self.collection.find({"role": "student"}))

    def get_students_by_course(self, course_id):
        """
        Get all students enrolled in a specific course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            list: List of student documents
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        return list(self.collection.find({
            "role": "student",
            "enrolled_courses": course_id
        }))

    def get_pending_teachers(self):
        """
        Get all teachers pending approval

        Returns:
            list: List of teacher documents awaiting approval
        """
        return list(self.collection.find({
            "role": "teacher",
            "approved": False
        }).sort("created_at", -1))
