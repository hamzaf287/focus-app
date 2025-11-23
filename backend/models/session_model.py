"""
Session Model
Handles focus detection session data
"""

from bson.objectid import ObjectId
from datetime import datetime


class Session:
    """Session model for managing focus detection sessions"""

    def __init__(self, db):
        """Initialize with database connection"""
        self.collection = db.sessions

    def create_session(self, course_id, teacher_id, session_name=None):
        """
        Create a new focus detection session

        Args:
            course_id (str or ObjectId): Course ID
            teacher_id (str or ObjectId): Teacher's user ID
            session_name (str, optional): Name for the session

        Returns:
            dict: Created session document
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        if isinstance(teacher_id, str):
            teacher_id = ObjectId(teacher_id)

        # Create session document
        session_doc = {
            "course_id": course_id,
            "teacher_id": teacher_id,
            "session_name": session_name or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            "start_time": datetime.utcnow(),
            "end_time": None,
            "status": "active",
            "created_at": datetime.utcnow()
        }

        # Insert into database
        result = self.collection.insert_one(session_doc)
        session_doc['_id'] = result.inserted_id

        return session_doc

    def find_by_id(self, session_id):
        """
        Find session by ID

        Args:
            session_id (str or ObjectId): Session ID

        Returns:
            dict: Session document or None
        """
        if isinstance(session_id, str):
            session_id = ObjectId(session_id)
        return self.collection.find_one({"_id": session_id})

    def end_session(self, session_id):
        """
        Mark a session as completed

        Args:
            session_id (str or ObjectId): Session ID

        Returns:
            bool: True if updated successfully
        """
        if isinstance(session_id, str):
            session_id = ObjectId(session_id)

        result = self.collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "end_time": datetime.utcnow(),
                    "status": "completed"
                }
            }
        )
        return result.modified_count > 0

    def get_sessions_by_course(self, course_id, status=None):
        """
        Get all sessions for a specific course

        Args:
            course_id (str or ObjectId): Course ID
            status (str, optional): Filter by status ('active' or 'completed')

        Returns:
            list: List of session documents
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        query = {"course_id": course_id}
        if status:
            query["status"] = status

        return list(self.collection.find(query).sort("start_time", -1))

    def get_sessions_by_teacher(self, teacher_id, status=None):
        """
        Get all sessions created by a specific teacher

        Args:
            teacher_id (str or ObjectId): Teacher's user ID
            status (str, optional): Filter by status ('active' or 'completed')

        Returns:
            list: List of session documents
        """
        if isinstance(teacher_id, str):
            teacher_id = ObjectId(teacher_id)

        query = {"teacher_id": teacher_id}
        if status:
            query["status"] = status

        return list(self.collection.find(query).sort("start_time", -1))

    def get_active_session_by_course(self, course_id):
        """
        Get the currently active session for a course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            dict: Active session document or None
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        return self.collection.find_one({
            "course_id": course_id,
            "status": "active"
        })

    def get_all_active_sessions(self):
        """
        Get all active sessions

        Returns:
            list: List of active session documents
        """
        return list(self.collection.find({"status": "active"}).sort("start_time", -1))

    def update_session(self, session_id, updates):
        """
        Update session information

        Args:
            session_id (str or ObjectId): Session ID
            updates (dict): Fields to update

        Returns:
            bool: True if updated successfully
        """
        if isinstance(session_id, str):
            session_id = ObjectId(session_id)

        result = self.collection.update_one(
            {"_id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    def delete_session(self, session_id):
        """
        Delete a session

        Args:
            session_id (str or ObjectId): Session ID

        Returns:
            bool: True if deleted successfully
        """
        if isinstance(session_id, str):
            session_id = ObjectId(session_id)

        result = self.collection.delete_one({"_id": session_id})
        return result.deleted_count > 0

    def get_session_duration(self, session_id):
        """
        Calculate session duration in seconds

        Args:
            session_id (str or ObjectId): Session ID

        Returns:
            int: Duration in seconds or None if session not found/not ended
        """
        session = self.find_by_id(session_id)
        if not session or not session.get('end_time'):
            return None

        duration = (session['end_time'] - session['start_time']).total_seconds()
        return int(duration)
