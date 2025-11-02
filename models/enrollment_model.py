"""
Enrollment Request Model
Handles student enrollment requests and approvals
"""

from bson.objectid import ObjectId
from datetime import datetime


class EnrollmentRequest:
    """EnrollmentRequest model for managing course enrollment approvals"""

    def __init__(self, db):
        """Initialize with database connection"""
        self.collection = db.enrollment_requests

    def create_request(self, student_id, course_id):
        """
        Create a new enrollment request

        Args:
            student_id (str or ObjectId): Student's user ID
            course_id (str or ObjectId): Course ID

        Returns:
            dict: Created enrollment request document or None if already exists
        """
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        # Check if request already exists
        existing = self.collection.find_one({
            "student_id": student_id,
            "course_id": course_id,
            "status": {"$in": ["pending", "approved"]}
        })
        if existing:
            return None

        # Create enrollment request
        request_doc = {
            "student_id": student_id,
            "course_id": course_id,
            "status": "pending",  # pending, approved, rejected
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = self.collection.insert_one(request_doc)
        request_doc['_id'] = result.inserted_id

        return request_doc

    def find_by_id(self, request_id):
        """
        Find enrollment request by ID

        Args:
            request_id (str or ObjectId): Request ID

        Returns:
            dict: Enrollment request document or None
        """
        if isinstance(request_id, str):
            request_id = ObjectId(request_id)
        return self.collection.find_one({"_id": request_id})

    def get_requests_by_student(self, student_id):
        """
        Get all enrollment requests for a student

        Args:
            student_id (str or ObjectId): Student's user ID

        Returns:
            list: List of enrollment request documents
        """
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)

        return list(self.collection.find({"student_id": student_id}).sort("created_at", -1))

    def get_pending_requests_by_course(self, course_id):
        """
        Get all pending enrollment requests for a course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            list: List of pending enrollment request documents
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        return list(self.collection.find({
            "course_id": course_id,
            "status": "pending"
        }).sort("created_at", -1))

    def get_pending_requests_by_teacher(self, teacher_id, course_model):
        """
        Get all pending enrollment requests for a teacher's courses

        Args:
            teacher_id (str or ObjectId): Teacher's user ID
            course_model: Course model instance

        Returns:
            list: List of pending enrollment requests with course details
        """
        if isinstance(teacher_id, str):
            teacher_id = ObjectId(teacher_id)

        # Get all courses taught by this teacher
        courses = course_model.get_courses_by_teacher(str(teacher_id))

        all_requests = []
        for course in courses:
            requests = self.get_pending_requests_by_course(str(course['_id']))
            for request in requests:
                request['course'] = course
                all_requests.append(request)

        return all_requests

    def update_status(self, request_id, status, user_model=None):
        """
        Update enrollment request status

        Args:
            request_id (str or ObjectId): Request ID
            status (str): New status - 'approved' or 'rejected'
            user_model: User model instance (required for approved status)

        Returns:
            bool: True if updated successfully
        """
        if isinstance(request_id, str):
            request_id = ObjectId(request_id)

        # Get the request
        request = self.find_by_id(request_id)
        if not request:
            return False

        # Update request status
        result = self.collection.update_one(
            {"_id": request_id},
            {"$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }}
        )

        # If approved, also enroll student in course
        if status == "approved" and user_model:
            user_model.enroll_student_in_course(
                str(request['student_id']),
                str(request['course_id'])
            )

        return result.modified_count > 0

    def delete_request(self, request_id):
        """
        Delete an enrollment request

        Args:
            request_id (str or ObjectId): Request ID

        Returns:
            bool: True if deleted successfully
        """
        if isinstance(request_id, str):
            request_id = ObjectId(request_id)

        result = self.collection.delete_one({"_id": request_id})
        return result.deleted_count > 0

    def get_approved_courses_by_student(self, student_id):
        """
        Get all approved courses for a student

        Args:
            student_id (str or ObjectId): Student's user ID

        Returns:
            list: List of course IDs where enrollment is approved
        """
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)

        approved_requests = self.collection.find({
            "student_id": student_id,
            "status": "approved"
        })

        return [str(req['course_id']) for req in approved_requests]
