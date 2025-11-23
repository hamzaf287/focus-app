"""
Student Routes
Handles student-specific operations: enroll in courses, join sessions, view reports
"""

from flask import Blueprint, request, jsonify, session
from bson.objectid import ObjectId

# Create Blueprint
student_bp = Blueprint('student', __name__, url_prefix='/student')

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


def student_required(f):
    """Decorator to require student role"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        user = user_model.find_by_id(session['user_id'])
        if not user or user['role'] != 'student':
            return jsonify({"error": "Student access required"}), 403

        return f(*args, **kwargs)
    return decorated_function


@student_bp.route('/courses/available', methods=['GET'])
@student_required
def get_available_courses():
    """Get all available courses for enrollment"""
    try:
        all_courses = course_model.get_all_courses()

        # Get student's enrolled courses
        student_id = session['user_id']
        student = user_model.find_by_id(student_id)
        enrolled_course_ids = [str(cid) for cid in student.get('enrolled_courses', [])]

        courses_list = []
        for course in all_courses:
            # Get teacher info
            teacher = user_model.find_by_id(course['teacher_id'])

            courses_list.append({
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name'],
                "teacher": {
                    "name": teacher['name']
                } if teacher else None,
                "student_count": len(course.get('students', [])),
                "is_enrolled": str(course['_id']) in enrolled_course_ids
            })

        return jsonify({"courses": courses_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch courses: {str(e)}"}), 500


@student_bp.route('/courses/enrolled', methods=['GET'])
@student_required
def get_enrolled_courses():
    """Get courses the student is enrolled in"""
    try:
        student_id = session['user_id']
        courses = course_model.get_courses_by_student(student_id)

        courses_list = []
        for course in courses:
            # Get teacher info
            teacher = user_model.find_by_id(course['teacher_id'])

            # Check if there's an active session
            active_session = session_model.get_active_session_by_course(course['_id'])

            courses_list.append({
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name'],
                "teacher": {
                    "name": teacher['name']
                } if teacher else None,
                "has_active_session": active_session is not None,
                "active_session_id": str(active_session['_id']) if active_session else None
            })

        return jsonify({"courses": courses_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch enrolled courses: {str(e)}"}), 500


@student_bp.route('/courses/<course_id>/enroll', methods=['POST'])
@student_required
def enroll_in_course(course_id):
    """
    Request enrollment in a course (creates an enrollment request for teacher approval)

    URL Parameter:
        course_id: ID of the course to request enrollment in
    """
    try:
        student_id = session['user_id']

        # Check if course exists
        course = course_model.find_by_id(course_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404

        # Check if already enrolled or request exists
        student = user_model.find_by_id(student_id)
        enrolled_courses = student.get('enrolled_courses', [])
        if ObjectId(course_id) in enrolled_courses:
            return jsonify({"error": "Already enrolled in this course"}), 409

        # Create enrollment request
        enrollment_request = enrollment_model.create_request(student_id, course_id)

        if not enrollment_request:
            return jsonify({"error": "Enrollment request already exists"}), 409

        return jsonify({
            "message": "Enrollment request submitted successfully. Waiting for teacher approval.",
            "request_id": str(enrollment_request['_id']),
            "status": "pending"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to request enrollment: {str(e)}"}), 500


@student_bp.route('/courses/<course_id>/unenroll', methods=['POST'])
@student_required
def unenroll_from_course(course_id):
    """
    Unenroll from a course

    URL Parameter:
        course_id: ID of the course to unenroll from
    """
    try:
        student_id = session['user_id']

        # Remove student from course
        course_model.remove_student(course_id, student_id)

        # Remove course from student's enrolled courses
        student = user_model.find_by_id(student_id)
        if student and 'enrolled_courses' in student:
            updated_courses = [cid for cid in student['enrolled_courses'] if str(cid) != course_id]
            user_model.collection.update_one(
                {"_id": ObjectId(student_id)},
                {"$set": {"enrolled_courses": updated_courses}}
            )

        return jsonify({"message": "Unenrolled successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to unenroll: {str(e)}"}), 500


@student_bp.route('/enrollment-requests', methods=['GET'])
@student_required
def get_enrollment_requests():
    """Get all enrollment requests for the student"""
    try:
        student_id = session['user_id']

        # Get all enrollment requests
        requests = enrollment_model.get_requests_by_student(student_id)

        requests_list = []
        for req in requests:
            course = course_model.find_by_id(str(req['course_id']))

            requests_list.append({
                "id": str(req['_id']),
                "status": req['status'],
                "created_at": req['created_at'].isoformat(),
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name']
                } if course else None
            })

        return jsonify({"requests": requests_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch enrollment requests: {str(e)}"}), 500


@student_bp.route('/sessions/active', methods=['GET'])
@student_required
def get_active_sessions():
    """
    Get all active sessions for courses the student is enrolled in

    Returns:
        JSON response with list of active sessions
    """
    try:
        student_id = session['user_id']

        # Get student's enrolled courses
        student = user_model.find_by_id(student_id)
        enrolled_course_ids = student.get('enrolled_courses', [])

        if not enrolled_course_ids:
            return jsonify({"sessions": []}), 200

        # Get all active sessions for enrolled courses
        active_sessions = []
        for course_id in enrolled_course_ids:
            # Get active sessions for this course
            sessions = session_model.get_sessions_by_course(str(course_id), status='active')

            for sess in sessions:
                # Get course info
                course = course_model.find_by_id(sess['course_id'])

                # Get teacher info
                teacher = user_model.find_by_id(sess['teacher_id'])

                active_sessions.append({
                    "id": str(sess['_id']),
                    "session_name": sess['session_name'],
                    "course": {
                        "id": str(course['_id']),
                        "course_code": course['course_code'],
                        "course_name": course['course_name']
                    } if course else None,
                    "teacher": {
                        "id": str(teacher['_id']),
                        "name": teacher['name']
                    } if teacher else None,
                    "start_time": sess['start_time'].isoformat(),
                    "status": sess['status']
                })

        return jsonify({"sessions": active_sessions}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch active sessions: {str(e)}"}), 500


@student_bp.route('/sessions/<session_id>/join', methods=['GET'])
@student_required
def join_session(session_id):
    """
    Get session information to join (start focus detection on client side)

    URL Parameter:
        session_id: ID of the session to join
    """
    try:
        student_id = session['user_id']

        # Get session
        session_obj = session_model.find_by_id(session_id)
        if not session_obj:
            return jsonify({"error": "Session not found"}), 404

        # Check if session is active
        if session_obj['status'] != 'active':
            return jsonify({"error": "Session is not active"}), 400

        # Get course info
        course = course_model.find_by_id(session_obj['course_id'])

        # Verify student is enrolled in the course
        student = user_model.find_by_id(student_id)
        if ObjectId(session_obj['course_id']) not in student.get('enrolled_courses', []):
            return jsonify({"error": "You are not enrolled in this course"}), 403

        return jsonify({
            "session": {
                "id": str(session_obj['_id']),
                "session_name": session_obj['session_name'],
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name']
                } if course else None,
                "start_time": session_obj['start_time'].isoformat(),
                "status": session_obj['status']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to join session: {str(e)}"}), 500


@student_bp.route('/reports', methods=['GET'])
@student_required
def get_my_reports():
    """Get all reports for the current student"""
    try:
        student_id = session['user_id']
        course_id = request.args.get('course_id')  # Optional filter

        reports = report_model.get_reports_by_student(student_id, course_id)

        reports_list = []
        for report in reports:
            # Get course and session info
            course = course_model.find_by_id(report['course_id'])
            session_obj = session_model.find_by_id(report['session_id'])

            reports_list.append({
                "id": str(report['_id']),
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name']
                } if course else None,
                "session": {
                    "id": str(session_obj['_id']),
                    "session_name": session_obj['session_name']
                } if session_obj else None,
                "focus_percentage": report['focus_percentage'],
                "focused_frames": report.get('focused_frames', 0),
                "distracted_frames": report.get('distracted_frames', 0),
                "total_frames": report.get('total_frames', 0),
                "duration": report.get('duration', 0),
                "tab_switches_count": len(report.get('tab_switches', [])),
                "report_path": report.get('report_path'),
                "created_at": report['created_at'].isoformat()
            })

        return jsonify({"reports": reports_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch reports: {str(e)}"}), 500


@student_bp.route('/reports/<report_id>', methods=['GET'])
@student_required
def get_report_details(report_id):
    """Get detailed information for a specific report"""
    try:
        student_id = session['user_id']

        # Get report
        report = report_model.find_by_id(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404

        # Verify student owns this report
        if str(report['student_id']) != student_id:
            return jsonify({"error": "Unauthorized access to this report"}), 403

        # Get related information
        course = course_model.find_by_id(report['course_id'])
        session_obj = session_model.find_by_id(report['session_id'])

        return jsonify({
            "report": {
                "id": str(report['_id']),
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name']
                } if course else None,
                "session": {
                    "id": str(session_obj['_id']),
                    "session_name": session_obj['session_name'],
                    "start_time": session_obj['start_time'].isoformat(),
                    "end_time": session_obj['end_time'].isoformat() if session_obj.get('end_time') else None
                } if session_obj else None,
                "focus_percentage": report['focus_percentage'],
                "focused_frames": report.get('focused_frames', 0),
                "distracted_frames": report.get('distracted_frames', 0),
                "total_frames": report.get('total_frames', 0),
                "duration": report.get('duration', 0),
                "tab_switches": report.get('tab_switches', []),
                "tab_switches_count": len(report.get('tab_switches', [])),
                "report_path": report.get('report_path'),
                "created_at": report['created_at'].isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch report details: {str(e)}"}), 500


@student_bp.route('/reports/<report_id>/download', methods=['GET'])
@student_required
def download_report_pdf(report_id):
    """
    Download PDF report for a specific report

    URL Parameter:
        report_id: ID of the report to download
    """
    try:
        from flask import send_file
        import os

        student_id = session['user_id']

        # Get report
        report = report_model.find_by_id(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404

        # Verify student owns this report
        if str(report['student_id']) != student_id:
            return jsonify({"error": "Unauthorized access to this report"}), 403

        # Check if PDF already exists
        if report.get('report_path') and os.path.exists(report['report_path']):
            return send_file(report['report_path'], as_attachment=True,
                           download_name=f"focus_report_{report_id}.pdf")

        # Generate PDF if it doesn't exist
        from datetime import datetime
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER
        from config import config
        import os as os_module

        # Get related data
        student = user_model.find_by_id(str(report['student_id']))
        course = course_model.find_by_id(str(report['course_id']))
        session_obj = session_model.find_by_id(str(report['session_id']))

        if not student or not course or not session_obj:
            return jsonify({"error": "Related data not found"}), 404

        # Generate PDF
        pdf_filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        reports_folder = os_module.environ.get('REPORTS_FOLDER', 'static/reports')
        os_module.makedirs(reports_folder, exist_ok=True)
        pdf_path = os_module.path.join(reports_folder, pdf_filename)

        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Add custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=12
        )

        # Title
        story.append(Paragraph("Focus Detection Report", title_style))
        story.append(Spacer(1, 0.3*inch))

        # Student Information
        story.append(Paragraph("Student Information", heading_style))
        student_data = [
            ['Student Name:', student['name']],
            ['Email:', student['email']],
            ['Report Date:', report['created_at'].strftime('%Y-%m-%d %H:%M:%S')]
        ]
        student_table = Table(student_data, colWidths=[2*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        story.append(student_table)
        story.append(Spacer(1, 0.3*inch))

        # Session Information
        story.append(Paragraph("Session Information", heading_style))
        session_data = [
            ['Course:', f"{course['course_code']} - {course['course_name']}"],
            ['Session:', session_obj['session_name']],
            ['Duration:', f"{report['duration'] // 60} min {report['duration'] % 60} sec"]
        ]
        session_table = Table(session_data, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        story.append(session_table)
        story.append(Spacer(1, 0.3*inch))

        # Focus Statistics
        story.append(Paragraph("Focus Statistics", heading_style))

        # Determine focus grade
        focus_pct = report['focus_percentage']
        if focus_pct >= 80:
            grade = "Excellent"
            grade_color = colors.HexColor('#10b981')
        elif focus_pct >= 60:
            grade = "Good"
            grade_color = colors.HexColor('#f59e0b')
        else:
            grade = "Needs Improvement"
            grade_color = colors.HexColor('#ef4444')

        stats_data = [
            ['Focus Percentage:', f"{focus_pct}%", grade],
            ['Focused Frames:', str(report['focused_frames']), ''],
            ['Distracted Frames:', str(report['distracted_frames']), ''],
            ['Total Frames Analyzed:', str(report['total_frames']), ''],
            ['Tab Switches:', str(len(report.get('tab_switches', []))), '']
        ]
        stats_table = Table(stats_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (2, 0), (2, 0), grade_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.5*inch))

        # Footer
        footer_text = f"Generated by FocusCheck | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(footer_text, footer_style))

        # Build PDF
        doc.build(story)

        # Update report with PDF path
        report_model.update_report_path(report_id, pdf_path)

        return send_file(pdf_path, as_attachment=True,
                        download_name=f"focus_report_{report_id}.pdf")

    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


@student_bp.route('/statistics', methods=['GET'])
@student_required
def get_my_statistics():
    """Get overall statistics for the current student"""
    try:
        student_id = session['user_id']

        # Get enrolled courses
        courses = course_model.get_courses_by_student(student_id)

        # Get all reports
        all_reports = report_model.get_reports_by_student(student_id)

        # Calculate overall average
        overall_avg = report_model.get_student_average_focus(student_id)

        # Get per-course statistics
        course_stats = []
        for course in courses:
            course_avg = report_model.get_student_average_focus(student_id, course['_id'])
            course_reports = report_model.get_reports_by_student(student_id, course['_id'])

            course_stats.append({
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name']
                },
                "average_focus": course_avg,
                "total_sessions": len(course_reports)
            })

        return jsonify({
            "statistics": {
                "overall_average_focus": overall_avg,
                "total_reports": len(all_reports),
                "enrolled_courses": len(courses),
                "course_statistics": course_stats
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch statistics: {str(e)}"}), 500
