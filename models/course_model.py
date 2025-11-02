"""
Course Model
Handles course data and student enrollment
"""

from bson.objectid import ObjectId
from datetime import datetime


class Course:
    """Course model for managing courses and enrollments"""

    def __init__(self, db):
        """Initialize with database connection"""
        self.collection = db.courses

    def create_course(self, course_code, course_name, teacher_id):
        """
        Create a new course

        Args:
            course_code (str): Unique course code (e.g., 'CSCS460ASP2024')
            course_name (str): Course name
            teacher_id (str or ObjectId): Teacher's user ID

        Returns:
            dict: Created course document or None if course_code exists
        """
        # Check if course code already exists
        if self.collection.find_one({"course_code": course_code}):
            return None

        if isinstance(teacher_id, str):
            teacher_id = ObjectId(teacher_id)

        # Create course document
        course_doc = {
            "course_code": course_code,
            "course_name": course_name,
            "teacher_id": teacher_id,
            "students": [],
            "created_at": datetime.utcnow()
        }

        # Insert into database
        result = self.collection.insert_one(course_doc)
        course_doc['_id'] = result.inserted_id

        return course_doc

    def find_by_id(self, course_id):
        """
        Find course by ID

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            dict: Course document or None
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        return self.collection.find_one({"_id": course_id})

    def find_by_code(self, course_code):
        """
        Find course by course code

        Args:
            course_code (str): Course code

        Returns:
            dict: Course document or None
        """
        return self.collection.find_one({"course_code": course_code})

    def get_courses_by_teacher(self, teacher_id):
        """
        Get all courses taught by a specific teacher

        Args:
            teacher_id (str or ObjectId): Teacher's user ID

        Returns:
            list: List of course documents
        """
        if isinstance(teacher_id, str):
            teacher_id = ObjectId(teacher_id)

        return list(self.collection.find({"teacher_id": teacher_id}))

    def get_courses_by_student(self, student_id):
        """
        Get all courses a student is enrolled in

        Args:
            student_id (str or ObjectId): Student's user ID

        Returns:
            list: List of course documents
        """
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)

        return list(self.collection.find({"students": student_id}))

    def enroll_student(self, course_id, student_id):
        """
        Enroll a student in a course

        Args:
            course_id (str or ObjectId): Course ID
            student_id (str or ObjectId): Student's user ID

        Returns:
            bool: True if enrolled successfully
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)

        result = self.collection.update_one(
            {"_id": course_id},
            {"$addToSet": {"students": student_id}}
        )
        return result.modified_count > 0

    def remove_student(self, course_id, student_id):
        """
        Remove a student from a course

        Args:
            course_id (str or ObjectId): Course ID
            student_id (str or ObjectId): Student's user ID

        Returns:
            bool: True if removed successfully
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)

        result = self.collection.update_one(
            {"_id": course_id},
            {"$pull": {"students": student_id}}
        )
        return result.modified_count > 0

    def get_all_courses(self):
        """
        Get all courses

        Returns:
            list: List of all course documents
        """
        return list(self.collection.find({}))

    def update_course(self, course_id, updates):
        """
        Update course information

        Args:
            course_id (str or ObjectId): Course ID
            updates (dict): Fields to update

        Returns:
            bool: True if updated successfully
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        result = self.collection.update_one(
            {"_id": course_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_course(self, course_id):
        """
        Delete a course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            bool: True if deleted successfully
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        result = self.collection.delete_one({"_id": course_id})
        return result.deleted_count > 0

    def get_student_count(self, course_id):
        """
        Get number of students enrolled in a course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            int: Number of enrolled students
        """
        course = self.find_by_id(course_id)
        return len(course.get('students', [])) if course else 0
