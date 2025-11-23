"""
Admin Routes
Handles admin-specific operations: approve teachers, manage courses
"""

from flask import Blueprint, request, jsonify, session
from bson.objectid import ObjectId

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Models will be injected via init_routes function
user_model = None
course_model = None
session_model = None
report_model = None
enrollment_model = None


def init_routes(db):
    """Initialize routes with database models"""
    global user_model, course_model, session_model, report_model, enrollment_model
    from models.user_model import User
    from models.course_model import Course
    from models.session_model import Session
    from models.report_model import FocusReport
    from models.enrollment_model import EnrollmentRequest
    user_model = User(db)
    course_model = Course(db)
    session_model = Session(db)
    report_model = FocusReport(db)
    enrollment_model = EnrollmentRequest(db)


def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        user = user_model.find_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/teachers/pending', methods=['GET'])
@admin_required
def get_pending_teachers():
    """Get all teachers pending approval"""
    try:
        teachers = user_model.get_pending_teachers()

        teachers_list = []
        for teacher in teachers:
            teachers_list.append({
                "id": str(teacher['_id']),
                "name": teacher['name'],
                "email": teacher['email'],
                "created_at": teacher.get('created_at').isoformat() if teacher.get('created_at') else None
            })

        return jsonify({"teachers": teachers_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch pending teachers: {str(e)}"}), 500


@admin_bp.route('/teachers/approve/<teacher_id>', methods=['POST'])
@admin_required
def approve_teacher(teacher_id):
    """
    Approve a teacher account

    URL Parameter:
        teacher_id: ID of the teacher to approve
    """
    try:
        # Approve the teacher
        success = user_model.update_approval_status(teacher_id, True)

        if not success:
            return jsonify({"error": "Teacher not found or already approved"}), 404

        return jsonify({"message": "Teacher approved successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to approve teacher: {str(e)}"}), 500


@admin_bp.route('/teachers/reject/<teacher_id>', methods=['POST'])
@admin_required
def reject_teacher(teacher_id):
    """
    Reject/disapprove a teacher account

    URL Parameter:
        teacher_id: ID of the teacher to reject
    """
    try:
        # Set approval to false
        success = user_model.update_approval_status(teacher_id, False)

        if not success:
            return jsonify({"error": "Teacher not found"}), 404

        return jsonify({"message": "Teacher rejected"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to reject teacher: {str(e)}"}), 500


@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_all_students():
    """Get all students"""
    try:
        students = user_model.get_all_students()

        students_list = []
        for student in students:
            # Get enrolled courses
            enrolled_courses = []
            for course_id in student.get('enrolled_courses', []):
                course = course_model.find_by_id(course_id)
                if course:
                    enrolled_courses.append({
                        "id": str(course['_id']),
                        "course_code": course['course_code'],
                        "course_name": course['course_name']
                    })

            students_list.append({
                "id": str(student['_id']),
                "name": student['name'],
                "email": student['email'],
                "enrolled_courses": enrolled_courses
            })

        return jsonify({"students": students_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch students: {str(e)}"}), 500


@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """Get system statistics for admin dashboard"""
    try:
        # Count users by role
        all_students = user_model.get_all_students()
        pending_teachers = user_model.get_pending_teachers()
        all_courses = course_model.get_all_courses()

        # Count approved teachers
        from models.user_model import User
        temp_user_model = User(user_model.collection.database)
        approved_teachers = list(temp_user_model.collection.find({"role": "teacher", "approved": True}))

        return jsonify({
            "total_students": len(all_students),
            "total_teachers": len(approved_teachers),
            "pending_teachers": len(pending_teachers),
            "total_courses": len(all_courses)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch statistics: {str(e)}"}), 500


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """
    Get all users grouped by role with course information

    Returns:
    {
        "teachers": [{
            "id": "...", "name": "...", "email": "...", "status": "approved/pending",
            "created_at": "...",
            "courses": [{"id": "...", "course_code": "...", "course_name": "...", "student_count": 0}]
        }],
        "students": [{
            "id": "...", "name": "...", "email": "...",
            "created_at": "...",
            "courses": [{"id": "...", "course_code": "...", "course_name": "..."}]
        }]
    }
    """
    try:
        # Get all teachers (both approved and pending)
        from models.user_model import User
        temp_user_model = User(user_model.collection.database)
        all_teachers = list(temp_user_model.collection.find({"role": "teacher"}))

        teachers_list = []
        for teacher in all_teachers:
            teacher_id = str(teacher['_id'])

            # Get courses taught by this teacher
            teacher_courses = course_model.get_courses_by_teacher(teacher_id)
            courses_list = []
            for course in teacher_courses:
                courses_list.append({
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name'],
                    "student_count": len(course.get('students', []))
                })

            teachers_list.append({
                "id": teacher_id,
                "name": teacher['name'],
                "email": teacher['email'],
                "status": "approved" if teacher.get('approved', False) else "pending",
                "created_at": teacher.get('created_at').isoformat() if teacher.get('created_at') else None,
                "courses": courses_list
            })

        # Get all students
        all_students = user_model.get_all_students()

        students_list = []
        for student in all_students:
            # Resolve enrolled courses
            enrolled_courses = student.get('enrolled_courses', [])
            courses_list = []
            for course_id in enrolled_courses:
                course = course_model.find_by_id(str(course_id))
                if course:
                    courses_list.append({
                        "id": str(course['_id']),
                        "course_code": course['course_code'],
                        "course_name": course['course_name']
                    })

            students_list.append({
                "id": str(student['_id']),
                "name": student['name'],
                "email": student['email'],
                "created_at": student.get('created_at').isoformat() if student.get('created_at') else None,
                "courses": courses_list
            })

        return jsonify({
            "teachers": teachers_list,
            "students": students_list
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch users: {str(e)}"}), 500


@admin_bp.route('/teachers/<teacher_id>', methods=['DELETE'])
@admin_required
def delete_teacher(teacher_id):
    """
    Delete a teacher and cascade delete associated data

    This will:
    1. Delete all courses taught by the teacher
    2. Delete all sessions created by the teacher
    3. Delete all reports from those sessions
    4. Remove enrollment requests for those courses
    5. Delete the teacher account

    URL Parameter:
        teacher_id: ID of the teacher to delete
    """
    try:
        # Verify teacher exists
        teacher = user_model.find_by_id(teacher_id)
        if not teacher or teacher['role'] != 'teacher':
            return jsonify({"error": "Teacher not found"}), 404

        # Get all courses taught by this teacher
        courses = course_model.get_courses_by_teacher(teacher_id)
        course_ids = [str(course['_id']) for course in courses]

        # Delete associated data
        for course_id in course_ids:
            # Get all sessions for this course
            sessions = session_model.get_sessions_by_course(course_id)

            for sess in sessions:
                session_id = str(sess['_id'])

                # Delete all reports for this session
                reports = report_model.get_reports_by_session(session_id)
                for report in reports:
                    report_model.collection.delete_one({'_id': report['_id']})

                # Delete the session
                session_model.collection.delete_one({'_id': sess['_id']})

            # Delete enrollment requests for this course
            enrollment_model.collection.delete_many({'course_id': ObjectId(course_id)})

            # Remove course from students' enrolled_courses
            course = course_model.find_by_id(course_id)
            if course:
                for student_id in course.get('students', []):
                    user_model.collection.update_one(
                        {'_id': ObjectId(str(student_id))},
                        {'$pull': {'enrolled_courses': ObjectId(course_id)}}
                    )

            # Delete the course
            course_model.delete_course(course_id)

        # Delete the teacher
        success = user_model.collection.delete_one({'_id': ObjectId(teacher_id)})

        if success.deleted_count == 0:
            return jsonify({"error": "Failed to delete teacher"}), 500

        return jsonify({
            "message": "Teacher and associated data deleted successfully",
            "deleted_courses": len(course_ids)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete teacher: {str(e)}"}), 500


@admin_bp.route('/students/<student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    """
    Delete a student and cascade delete associated data

    This will:
    1. Delete all reports created by the student
    2. Remove student from all enrolled courses
    3. Delete all enrollment requests by the student
    4. Delete the student account

    URL Parameter:
        student_id: ID of the student to delete
    """
    try:
        # Verify student exists
        student = user_model.find_by_id(student_id)
        if not student or student['role'] != 'student':
            return jsonify({"error": "Student not found"}), 404

        # Delete all reports created by this student
        report_model.collection.delete_many({'student_id': ObjectId(student_id)})

        # Get enrolled courses
        enrolled_courses = student.get('enrolled_courses', [])

        # Remove student from all courses
        for course_id in enrolled_courses:
            course_model.collection.update_one(
                {'_id': ObjectId(str(course_id))},
                {'$pull': {'students': ObjectId(student_id)}}
            )

        # Delete all enrollment requests by this student
        enrollment_model.collection.delete_many({'student_id': ObjectId(student_id)})

        # Delete the student
        success = user_model.collection.delete_one({'_id': ObjectId(student_id)})

        if success.deleted_count == 0:
            return jsonify({"error": "Failed to delete student"}), 500

        return jsonify({
            "message": "Student and associated data deleted successfully",
            "removed_from_courses": len(enrolled_courses)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete student: {str(e)}"}), 500


# ==================== COURSE MANAGEMENT ROUTES ====================

@admin_bp.route('/courses', methods=['GET'])
@admin_required
def get_all_courses():
    """
    Get all courses with teacher info and student count

    Returns:
    {
        "courses": [
            {
                "id": "...",
                "course_code": "...",
                "course_name": "...",
                "teacher_id": "...",
                "teacher_name": "...",
                "student_count": 0
            }
        ]
    }
    """
    try:
        courses = course_model.get_all_courses()

        courses_list = []
        for course in courses:
            # Get teacher info
            teacher = user_model.find_by_id(str(course['teacher_id']))
            teacher_name = teacher['name'] if teacher else "Unknown Teacher"

            # Get student count
            student_count = len(course.get('students', []))

            courses_list.append({
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name'],
                "teacher_id": str(course['teacher_id']),
                "teacher_name": teacher_name,
                "student_count": student_count,
                "created_at": course.get('created_at').isoformat() if course.get('created_at') else None
            })

        return jsonify({"courses": courses_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch courses: {str(e)}"}), 500


@admin_bp.route('/courses/add', methods=['POST'])
@admin_required
def add_course():
    """
    Add a new course

    Request Body:
    {
        "course_code": "CSCS460ASP2024",
        "course_name": "Software Engineering",
        "teacher_id": "teacher_id_here"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('course_code') or not data.get('course_name') or not data.get('teacher_id'):
            return jsonify({"error": "Missing required fields: course_code, course_name, teacher_id"}), 400

        course_code = data['course_code'].strip()
        course_name = data['course_name'].strip()
        teacher_id = data['teacher_id'].strip()

        # Check if course code already exists
        existing_course = course_model.find_by_code(course_code)
        if existing_course:
            return jsonify({"error": "Course code already exists"}), 409

        # Verify teacher exists and is approved
        teacher = user_model.find_by_id(teacher_id)
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404

        if teacher['role'] != 'teacher':
            return jsonify({"error": "User is not a teacher"}), 400

        if not teacher.get('approved', False):
            return jsonify({"error": "Teacher is not approved"}), 400

        # Create course
        course = course_model.create_course(course_code, course_name, teacher_id)

        if not course:
            return jsonify({"error": "Failed to create course"}), 500

        return jsonify({
            "message": "Course created successfully",
            "course": {
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name'],
                "teacher_id": str(course['teacher_id']),
                "teacher_name": teacher['name']
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to add course: {str(e)}"}), 500


@admin_bp.route('/courses/<course_id>', methods=['PUT'])
@admin_required
def edit_course(course_id):
    """
    Edit an existing course

    URL Parameter:
        course_id: ID of the course to edit

    Request Body:
    {
        "course_code": "CSCS460ASP2024",
        "course_name": "Software Engineering",
        "teacher_id": "teacher_id_here"
    }
    """
    try:
        data = request.get_json()

        # Verify course exists
        course = course_model.find_by_id(course_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404

        updates = {}

        # Validate and update course code if provided
        if 'course_code' in data:
            new_code = data['course_code'].strip()
            # Check if new code already exists (but not for this course)
            existing = course_model.find_by_code(new_code)
            if existing and str(existing['_id']) != course_id:
                return jsonify({"error": "Course code already exists"}), 409
            updates['course_code'] = new_code

        # Update course name if provided
        if 'course_name' in data:
            updates['course_name'] = data['course_name'].strip()

        # Validate and update teacher if provided
        if 'teacher_id' in data:
            teacher_id = data['teacher_id'].strip()
            teacher = user_model.find_by_id(teacher_id)

            if not teacher:
                return jsonify({"error": "Teacher not found"}), 404

            if teacher['role'] != 'teacher':
                return jsonify({"error": "User is not a teacher"}), 400

            if not teacher.get('approved', False):
                return jsonify({"error": "Teacher is not approved"}), 400

            updates['teacher_id'] = ObjectId(teacher_id)

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        # Update course
        success = course_model.update_course(course_id, updates)

        if not success:
            return jsonify({"error": "Failed to update course"}), 500

        # Get updated course
        updated_course = course_model.find_by_id(course_id)
        teacher = user_model.find_by_id(str(updated_course['teacher_id']))

        return jsonify({
            "message": "Course updated successfully",
            "course": {
                "id": str(updated_course['_id']),
                "course_code": updated_course['course_code'],
                "course_name": updated_course['course_name'],
                "teacher_id": str(updated_course['teacher_id']),
                "teacher_name": teacher['name'] if teacher else "Unknown"
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update course: {str(e)}"}), 500


@admin_bp.route('/courses/<course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """
    Delete a course and cascade delete associated data

    This will:
    1. Delete all sessions for the course
    2. Delete all reports from those sessions
    3. Remove enrollment requests for the course
    4. Remove course from students' enrolled_courses
    5. Delete the course

    URL Parameter:
        course_id: ID of the course to delete
    """
    try:
        # Verify course exists
        course = course_model.find_by_id(course_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404

        # Get all sessions for this course
        sessions = session_model.get_sessions_by_course(course_id)

        # Delete all reports and sessions
        for sess in sessions:
            session_id = str(sess['_id'])

            # Delete all reports for this session
            reports = report_model.get_reports_by_session(session_id)
            for report in reports:
                report_model.collection.delete_one({'_id': report['_id']})

            # Delete the session
            session_model.collection.delete_one({'_id': sess['_id']})

        # Delete enrollment requests for this course
        enrollment_model.collection.delete_many({'course_id': ObjectId(course_id)})

        # Remove course from students' enrolled_courses
        for student_id in course.get('students', []):
            user_model.collection.update_one(
                {'_id': ObjectId(str(student_id))},
                {'$pull': {'enrolled_courses': ObjectId(course_id)}}
            )

        # Delete the course
        success = course_model.delete_course(course_id)

        if not success:
            return jsonify({"error": "Failed to delete course"}), 500

        return jsonify({
            "message": "Course and associated data deleted successfully",
            "deleted_sessions": len(sessions),
            "students_unenrolled": len(course.get('students', []))
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete course: {str(e)}"}), 500


@admin_bp.route('/courses/<course_id>/students', methods=['GET'])
@admin_required
def get_course_students(course_id):
    """
    Get all students enrolled in a specific course

    URL Parameter:
        course_id: ID of the course

    Returns:
    {
        "course": {"id": "...", "course_code": "...", "course_name": "..."},
        "students": [{"id": "...", "name": "...", "email": "..."}]
    }
    """
    try:
        # Verify course exists
        course = course_model.find_by_id(course_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404

        # Get students
        students = user_model.get_students_by_course(course_id)

        students_list = []
        for student in students:
            students_list.append({
                "id": str(student['_id']),
                "name": student['name'],
                "email": student['email']
            })

        return jsonify({
            "course": {
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name']
            },
            "students": students_list
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch course students: {str(e)}"}), 500


@admin_bp.route('/teachers/approved', methods=['GET'])
@admin_required
def get_approved_teachers():
    """
    Get all approved teachers for dropdown selection

    Returns:
    {
        "teachers": [{"id": "...", "name": "...", "email": "..."}]
    }
    """
    try:
        teachers = user_model.get_approved_teachers()

        teachers_list = []
        for teacher in teachers:
            teachers_list.append({
                "id": str(teacher['_id']),
                "name": teacher['name'],
                "email": teacher['email']
            })

        return jsonify({"teachers": teachers_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch approved teachers: {str(e)}"}), 500
