"""
Focus Report Model
Handles focus detection report data and PDF generation tracking
"""

from bson.objectid import ObjectId
from datetime import datetime


class FocusReport:
    """FocusReport model for managing focus detection reports"""

    def __init__(self, db):
        """Initialize with database connection"""
        self.collection = db.focus_reports

    def create_report(self, student_id, course_id, session_id, focus_percentage,
                     report_path=None, focused_frames=0, distracted_frames=0,
                     total_frames=0, duration=0, tab_switches=None):
        """
        Create a new focus report

        Args:
            student_id (str or ObjectId): Student's user ID
            course_id (str or ObjectId): Course ID
            session_id (str or ObjectId): Session ID
            focus_percentage (float): Focus percentage (0-100)
            report_path (str, optional): Path to generated PDF report
            focused_frames (int): Number of focused frames detected
            distracted_frames (int): Number of distracted frames detected
            total_frames (int): Total frames analyzed
            duration (int): Session duration in seconds
            tab_switches (list, optional): List of tab/window switches

        Returns:
            dict: Created report document
        """
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)
        if isinstance(session_id, str):
            session_id = ObjectId(session_id)

        # Create report document
        report_doc = {
            "student_id": student_id,
            "course_id": course_id,
            "session_id": session_id,
            "focus_percentage": round(focus_percentage, 2),
            "focused_frames": focused_frames,
            "distracted_frames": distracted_frames,
            "total_frames": total_frames,
            "duration": duration,
            "tab_switches": tab_switches or [],
            "report_path": report_path,
            "created_at": datetime.utcnow()
        }

        # Insert into database
        result = self.collection.insert_one(report_doc)
        report_doc['_id'] = result.inserted_id

        return report_doc

    def find_by_id(self, report_id):
        """
        Find report by ID

        Args:
            report_id (str or ObjectId): Report ID

        Returns:
            dict: Report document or None
        """
        if isinstance(report_id, str):
            report_id = ObjectId(report_id)
        return self.collection.find_one({"_id": report_id})

    def get_reports_by_student(self, student_id, course_id=None):
        """
        Get all reports for a specific student

        Args:
            student_id (str or ObjectId): Student's user ID
            course_id (str or ObjectId, optional): Filter by course

        Returns:
            list: List of report documents
        """
        if isinstance(student_id, str):
            student_id = ObjectId(student_id)

        query = {"student_id": student_id}

        if course_id:
            if isinstance(course_id, str):
                course_id = ObjectId(course_id)
            query["course_id"] = course_id

        return list(self.collection.find(query).sort("created_at", -1))

    def get_reports_by_session(self, session_id):
        """
        Get all reports for a specific session

        Args:
            session_id (str or ObjectId): Session ID

        Returns:
            list: List of report documents
        """
        if isinstance(session_id, str):
            session_id = ObjectId(session_id)

        return list(self.collection.find({"session_id": session_id}).sort("focus_percentage", -1))

    def get_reports_by_course(self, course_id):
        """
        Get all reports for a specific course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            list: List of report documents
        """
        if isinstance(course_id, str):
            course_id = ObjectId(course_id)

        return list(self.collection.find({"course_id": course_id}).sort("created_at", -1))

    def update_report_path(self, report_id, report_path):
        """
        Update the PDF report path

        Args:
            report_id (str or ObjectId): Report ID
            report_path (str): Path to PDF report

        Returns:
            bool: True if updated successfully
        """
        if isinstance(report_id, str):
            report_id = ObjectId(report_id)

        result = self.collection.update_one(
            {"_id": report_id},
            {"$set": {"report_path": report_path}}
        )
        return result.modified_count > 0

    def get_student_average_focus(self, student_id, course_id=None):
        """
        Calculate average focus percentage for a student

        Args:
            student_id (str or ObjectId): Student's user ID
            course_id (str or ObjectId, optional): Filter by course

        Returns:
            float: Average focus percentage or 0 if no reports
        """
        reports = self.get_reports_by_student(student_id, course_id)

        if not reports:
            return 0.0

        total_focus = sum(report['focus_percentage'] for report in reports)
        return round(total_focus / len(reports), 2)

    def get_course_average_focus(self, course_id):
        """
        Calculate average focus percentage for all students in a course

        Args:
            course_id (str or ObjectId): Course ID

        Returns:
            float: Average focus percentage or 0 if no reports
        """
        reports = self.get_reports_by_course(course_id)

        if not reports:
            return 0.0

        total_focus = sum(report['focus_percentage'] for report in reports)
        return round(total_focus / len(reports), 2)

    def get_session_statistics(self, session_id):
        """
        Get statistics for a session (for teacher dashboard)

        Args:
            session_id (str or ObjectId): Session ID

        Returns:
            dict: Statistics including average focus, student count, etc.
        """
        reports = self.get_reports_by_session(session_id)

        if not reports:
            return {
                "student_count": 0,
                "average_focus": 0.0,
                "max_focus": 0.0,
                "min_focus": 0.0
            }

        focus_percentages = [r['focus_percentage'] for r in reports]

        return {
            "student_count": len(reports),
            "average_focus": round(sum(focus_percentages) / len(focus_percentages), 2),
            "max_focus": max(focus_percentages),
            "min_focus": min(focus_percentages)
        }

    def delete_report(self, report_id):
        """
        Delete a report

        Args:
            report_id (str or ObjectId): Report ID

        Returns:
            bool: True if deleted successfully
        """
        if isinstance(report_id, str):
            report_id = ObjectId(report_id)

        result = self.collection.delete_one({"_id": report_id})
        return result.deleted_count > 0

    def get_recent_reports(self, limit=10):
        """
        Get most recent reports across all students

        Args:
            limit (int): Maximum number of reports to return

        Returns:
            list: List of recent report documents
        """
        return list(self.collection.find().sort("created_at", -1).limit(limit))
