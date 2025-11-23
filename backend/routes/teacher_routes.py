"""
Teacher Routes
Handles teacher-specific operations: create sessions, view reports
"""

from flask import Blueprint, request, jsonify, session
from bson.objectid import ObjectId

# Create Blueprint
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

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


def teacher_required(f):
    """Decorator to require teacher role"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        user = user_model.find_by_id(session['user_id'])
        if not user or user['role'] != 'teacher':
            return jsonify({"error": "Teacher access required"}), 403

        if not user['approved']:
            return jsonify({"error": "Your account is pending approval"}), 403

        return f(*args, **kwargs)
    return decorated_function


@teacher_bp.route('/courses', methods=['GET'])
@teacher_required
def get_my_courses():
    """Get all courses taught by the current teacher"""
    try:
        teacher_id = session['user_id']
        courses = course_model.get_courses_by_teacher(teacher_id)

        courses_list = []
        for course in courses:
            courses_list.append({
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name'],
                "student_count": len(course.get('students', []))
            })

        return jsonify({"courses": courses_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch courses: {str(e)}"}), 500


@teacher_bp.route('/courses/<course_id>/students', methods=['GET'])
@teacher_required
def get_course_students(course_id):
    """Get all students enrolled in a specific course"""
    try:
        # Verify teacher owns this course
        course = course_model.find_by_id(course_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404

        if str(course['teacher_id']) != session['user_id']:
            return jsonify({"error": "Unauthorized access to this course"}), 403

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
                "course_name": course['course_name']
            },
            "students": students_list
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch students: {str(e)}"}), 500


@teacher_bp.route('/sessions', methods=['POST'])
@teacher_required
def create_session():
    """
    Create a new focus detection session

    Expected JSON:
    {
        "course_id": "course_object_id",
        "session_name": "Week 5 Lecture" (optional)
    }
    """
    try:
        # Check if teacher is approved
        teacher = user_model.find_by_id(session['user_id'])
        if not teacher or not teacher.get('approved', False):
            return jsonify({"error": "Your account must be approved by admin before creating sessions"}), 403

        data = request.get_json()

        # Validate required fields
        if 'course_id' not in data:
            return jsonify({"error": "Missing required field: course_id"}), 400

        course_id = data['course_id']
        session_name = data.get('session_name')

        # Verify teacher owns this course
        course = course_model.find_by_id(course_id)
        if not course or str(course['teacher_id']) != session['user_id']:
            return jsonify({"error": "Unauthorized access to this course"}), 403

        # Check if there's already an active session for this course
        active_session = session_model.get_active_session_by_course(course_id)
        if active_session:
            return jsonify({
                "error": "An active session already exists for this course",
                "session_id": str(active_session['_id'])
            }), 409

        # Create session
        new_session = session_model.create_session(
            course_id=course_id,
            teacher_id=session['user_id'],
            session_name=session_name
        )

        return jsonify({
            "message": "Session created successfully",
            "session": {
                "id": str(new_session['_id']),
                "session_name": new_session['session_name'],
                "course_id": str(new_session['course_id']),
                "start_time": new_session['start_time'].isoformat(),
                "status": new_session['status']
            }
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create session: {str(e)}"}), 500


@teacher_bp.route('/sessions/<session_id>/end', methods=['POST'])
@teacher_required
def end_session(session_id):
    """
    End an active session

    URL Parameter:
        session_id: ID of the session to end
    """
    try:
        # Verify teacher owns this session
        session_obj = session_model.find_by_id(session_id)
        if not session_obj or str(session_obj['teacher_id']) != session['user_id']:
            return jsonify({"error": "Unauthorized access to this session"}), 403

        # End the session
        success = session_model.end_session(session_id)

        if not success:
            return jsonify({"error": "Session not found or already ended"}), 404

        return jsonify({"message": "Session ended successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to end session: {str(e)}"}), 500


@teacher_bp.route('/sessions', methods=['GET'])
@teacher_required
def get_my_sessions():
    """Get all sessions created by the current teacher"""
    try:
        teacher_id = session['user_id']
        status = request.args.get('status')  # Optional filter: 'active' or 'completed'

        sessions = session_model.get_sessions_by_teacher(teacher_id, status)

        sessions_list = []
        for sess in sessions:
            # Get course info
            course = course_model.find_by_id(sess['course_id'])

            # Get session statistics
            stats = report_model.get_session_statistics(sess['_id'])

            sessions_list.append({
                "id": str(sess['_id']),
                "session_name": sess['session_name'],
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code'],
                    "course_name": course['course_name']
                } if course else None,
                "start_time": sess['start_time'].isoformat(),
                "end_time": sess['end_time'].isoformat() if sess['end_time'] else None,
                "status": sess['status'],
                "statistics": stats
            })

        return jsonify({"sessions": sessions_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch sessions: {str(e)}"}), 500


@teacher_bp.route('/sessions/<session_id>/reports', methods=['GET'])
@teacher_required
def get_session_reports(session_id):
    """Get all student reports for a specific session"""
    try:
        # Verify teacher owns this session
        session_obj = session_model.find_by_id(session_id)
        if not session_obj or str(session_obj['teacher_id']) != session['user_id']:
            return jsonify({"error": "Unauthorized access to this session"}), 403

        # Get reports
        reports = report_model.get_reports_by_session(session_id)

        reports_list = []
        for report in reports:
            # Get student info
            student = user_model.find_by_id(report['student_id'])

            reports_list.append({
                "id": str(report['_id']),
                "student": {
                    "id": str(student['_id']),
                    "name": student['name'],
                    "email": student['email']
                } if student else None,
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


@teacher_bp.route('/sessions/<session_id>/download', methods=['GET'])
@teacher_required
def download_session_combined_report(session_id):
    """
    Download combined PDF report for all students in a session

    This creates a comprehensive PDF containing:
    - Session overview (course, session name, date, duration)
    - Session statistics (total students, average focus, highest/lowest)
    - Individual student results in a table
    - Detailed breakdown for each student
    """
    try:
        from flask import send_file
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.colors import HexColor
        import os
        from datetime import datetime

        teacher_id = session['user_id']

        # Verify teacher owns this session
        session_obj = session_model.find_by_id(session_id)
        if not session_obj or str(session_obj['teacher_id']) != teacher_id:
            return jsonify({"error": "Unauthorized access to this session"}), 403

        # Get course info
        course = course_model.find_by_id(session_obj['course_id'])
        if not course:
            return jsonify({"error": "Course not found"}), 404

        # Check for existing combined PDF
        combined_pdf_filename = f"session_{session_id}_combined.pdf"
        combined_pdf_path = os.path.join('static', 'reports', combined_pdf_filename)

        # If PDF already exists, return it
        if os.path.exists(combined_pdf_path):
            return send_file(combined_pdf_path, as_attachment=True,
                           download_name=combined_pdf_filename)

        # Get all student reports for this session
        reports = report_model.get_reports_by_session(session_id)

        if not reports:
            return jsonify({"error": "No reports found for this session"}), 404

        # Get session statistics
        stats = report_model.get_session_statistics(session_id)

        # Create PDF
        os.makedirs(os.path.dirname(combined_pdf_path), exist_ok=True)
        doc = SimpleDocTemplate(combined_pdf_path, pagesize=letter)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#7c3aed'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#4a5568'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        # Title
        story.append(Paragraph(f"Combined Session Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Session Information Table
        session_data = [
            ['Course Code:', course['course_code']],
            ['Course Name:', course['course_name']],
            ['Session Name:', session_obj['session_name']],
            ['Date:', session_obj['start_time'].strftime('%Y-%m-%d')],
            ['Start Time:', session_obj['start_time'].strftime('%H:%M:%S')],
            ['End Time:', session_obj['end_time'].strftime('%H:%M:%S') if session_obj.get('end_time') else 'N/A'],
        ]

        session_table = Table(session_data, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph("Session Information", heading_style))
        story.append(session_table)
        story.append(Spacer(1, 0.3 * inch))

        # Session Statistics Table
        stats_data = [
            ['Total Students:', str(stats['student_count'])],
            ['Average Focus:', f"{stats['average_focus']:.1f}%"],
            ['Highest Focus:', f"{stats['max_focus']:.1f}%"],
            ['Lowest Focus:', f"{stats['min_focus']:.1f}%"],
        ]

        stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph("Session Statistics", heading_style))
        story.append(stats_table)
        story.append(Spacer(1, 0.4 * inch))

        # Student Results Summary Table
        story.append(Paragraph("Student Results", heading_style))

        # Build student results table
        student_results_data = [['#', 'Student Name', 'Focus %', 'Duration (min)', 'Grade']]

        for idx, report in enumerate(reports, 1):
            student = user_model.find_by_id(report['student_id'])
            student_name = student['name'] if student else 'Unknown'
            focus_pct = report['focus_percentage']
            duration_min = report.get('duration', 0) // 60

            # Determine grade
            if focus_pct >= 80:
                grade = 'Excellent'
            elif focus_pct >= 60:
                grade = 'Good'
            else:
                grade = 'Needs Improvement'

            student_results_data.append([
                str(idx),
                student_name,
                f"{focus_pct:.1f}%",
                str(duration_min),
                grade
            ])

        student_results_table = Table(student_results_data, colWidths=[0.5*inch, 2.5*inch, 1.2*inch, 1.3*inch, 1.5*inch])
        student_results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f9fafb')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(student_results_table)
        story.append(Spacer(1, 0.5 * inch))

        # Detailed breakdown for each student
        story.append(Paragraph("Detailed Student Reports", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        for idx, report in enumerate(reports, 1):
            student = user_model.find_by_id(report['student_id'])
            student_name = student['name'] if student else 'Unknown'

            # Student header
            student_header = Paragraph(f"{idx}. {student_name}", ParagraphStyle(
                'StudentHeader',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=HexColor('#7c3aed'),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            ))
            story.append(student_header)

            # Student details
            focus_pct = report['focus_percentage']
            focused_frames = report.get('focused_frames', 0)
            distracted_frames = report.get('distracted_frames', 0)
            total_frames = report.get('total_frames', 0)
            duration_sec = report.get('duration', 0)
            duration_min = duration_sec // 60

            # Determine grade and color
            if focus_pct >= 80:
                grade = 'Excellent'
                grade_color = HexColor('#10b981')
            elif focus_pct >= 60:
                grade = 'Good'
                grade_color = HexColor('#f59e0b')
            else:
                grade = 'Needs Improvement'
                grade_color = HexColor('#ef4444')

            student_detail_data = [
                ['Focus Percentage:', f"{focus_pct:.1f}%"],
                ['Grade:', grade],
                ['Focused Frames:', str(focused_frames)],
                ['Distracted Frames:', str(distracted_frames)],
                ['Total Frames:', str(total_frames)],
                ['Duration:', f"{duration_min} min {duration_sec % 60} sec"],
                ['Tab Switches:', str(len(report.get('tab_switches', [])))]
            ]

            student_detail_table = Table(student_detail_data, colWidths=[2*inch, 3*inch])
            student_detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('TEXTCOLOR', (1, 1), (1, 1), grade_color),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(student_detail_table)
            story.append(Spacer(1, 0.2 * inch))

        # Footer
        footer_text = f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
        story.append(Spacer(1, 0.3 * inch))
        story.append(footer)

        # Build PDF
        doc.build(story)

        return send_file(combined_pdf_path, as_attachment=True,
                        download_name=combined_pdf_filename)

    except Exception as e:
        return jsonify({"error": f"Failed to generate combined report: {str(e)}"}), 500


@teacher_bp.route('/reports/<report_id>/download', methods=['GET'])
@teacher_required
def download_student_report(report_id):
    """
    Download individual student PDF report (teacher access)

    Teacher can download any student report from their courses
    """
    try:
        from flask import send_file
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.colors import HexColor
        import os
        from datetime import datetime

        teacher_id = session['user_id']

        # Get report
        report = report_model.find_by_id(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404

        # Verify teacher owns the course/session
        session_obj = session_model.find_by_id(report['session_id'])
        if not session_obj or str(session_obj['teacher_id']) != teacher_id:
            return jsonify({"error": "Unauthorized access to this report"}), 403

        # Check if PDF already exists
        if report.get('report_path') and os.path.exists(report['report_path']):
            return send_file(report['report_path'], as_attachment=True,
                           download_name=f"focus_report_{report_id}.pdf")

        # Generate PDF
        student = user_model.find_by_id(report['student_id'])
        course = course_model.find_by_id(report['course_id'])

        if not student or not course:
            return jsonify({"error": "Student or course not found"}), 404

        # Create PDF
        pdf_filename = f"report_{report_id}.pdf"
        pdf_path = os.path.join('static', 'reports', pdf_filename)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#7c3aed'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#4a5568'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        # Title
        story.append(Paragraph("Focus Detection Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Student Information
        student_data = [
            ['Student Name:', student['name']],
            ['Email:', student['email']],
            ['Report Date:', report['created_at'].strftime('%Y-%m-%d %H:%M:%S')]
        ]

        student_table = Table(student_data, colWidths=[2*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph("Student Information", heading_style))
        story.append(student_table)
        story.append(Spacer(1, 0.3 * inch))

        # Session Information
        session_data = [
            ['Course:', f"{course['course_code']} - {course['course_name']}"],
            ['Session:', session_obj['session_name']],
            ['Duration:', f"{report.get('duration', 0) // 60} min {report.get('duration', 0) % 60} sec"]
        ]

        session_table = Table(session_data, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph("Session Information", heading_style))
        story.append(session_table)
        story.append(Spacer(1, 0.3 * inch))

        # Focus Statistics
        focus_pct = report['focus_percentage']

        # Determine grade and color
        if focus_pct >= 80:
            grade = 'Excellent'
            grade_color = HexColor('#10b981')
        elif focus_pct >= 60:
            grade = 'Good'
            grade_color = HexColor('#f59e0b')
        else:
            grade = 'Needs Improvement'
            grade_color = HexColor('#ef4444')

        focus_data = [
            ['Focus Percentage:', f"{focus_pct:.2f}%"],
            ['Grade:', grade],
            ['Focused Frames:', str(report.get('focused_frames', 0))],
            ['Distracted Frames:', str(report.get('distracted_frames', 0))],
            ['Total Frames:', str(report.get('total_frames', 0))],
            ['Tab Switches:', str(len(report.get('tab_switches', [])))]
        ]

        focus_table = Table(focus_data, colWidths=[2*inch, 4*inch])
        focus_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (1, 1), (1, 1), grade_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph("Focus Statistics", heading_style))
        story.append(focus_table)
        story.append(Spacer(1, 0.5 * inch))

        # Footer
        footer_text = f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
        story.append(footer)

        # Build PDF
        doc.build(story)

        # Update report path in database
        report_model.update_report_path(report_id, pdf_path)

        return send_file(pdf_path, as_attachment=True,
                        download_name=f"focus_report_{report_id}.pdf")

    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500


@teacher_bp.route('/courses/<course_id>/statistics', methods=['GET'])
@teacher_required
def get_course_statistics(course_id):
    """Get overall statistics for a course"""
    try:
        # Verify teacher owns this course
        course = course_model.find_by_id(course_id)
        if not course or str(course['teacher_id']) != session['user_id']:
            return jsonify({"error": "Unauthorized access to this course"}), 403

        # Get course average focus
        avg_focus = report_model.get_course_average_focus(course_id)

        # Get all sessions for this course
        sessions = session_model.get_sessions_by_course(course_id)

        # Get total number of reports
        reports = report_model.get_reports_by_course(course_id)

        return jsonify({
            "course": {
                "id": str(course['_id']),
                "course_code": course['course_code'],
                "course_name": course['course_name']
            },
            "statistics": {
                "average_focus": avg_focus,
                "total_sessions": len(sessions),
                "active_sessions": len([s for s in sessions if s['status'] == 'active']),
                "completed_sessions": len([s for s in sessions if s['status'] == 'completed']),
                "total_reports": len(reports),
                "student_count": len(course.get('students', []))
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch course statistics: {str(e)}"}), 500


@teacher_bp.route('/reports', methods=['GET'])
@teacher_required
def get_all_reports():
    """Get all reports for courses taught by this teacher"""
    try:
        teacher_id = session['user_id']

        # Get all teacher's courses
        courses = course_model.get_courses_by_teacher(teacher_id)

        all_reports = []
        for course in courses:
            reports = report_model.get_reports_by_course(course['_id'])
            all_reports.extend(reports)

        # Sort by created_at descending
        all_reports.sort(key=lambda x: x['created_at'], reverse=True)

        # Limit to recent reports (optional)
        limit = request.args.get('limit', type=int)
        if limit:
            all_reports = all_reports[:limit]

        reports_list = []
        for report in all_reports:
            # Get student and course info
            student = user_model.find_by_id(report['student_id'])
            course = course_model.find_by_id(report['course_id'])

            reports_list.append({
                "id": str(report['_id']),
                "student": {
                    "id": str(student['_id']),
                    "name": student['name']
                } if student else None,
                "course": {
                    "id": str(course['_id']),
                    "course_code": course['course_code']
                } if course else None,
                "focus_percentage": report['focus_percentage'],
                "created_at": report['created_at'].isoformat()
            })

        return jsonify({"reports": reports_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch reports: {str(e)}"}), 500


@teacher_bp.route('/enrollment-requests', methods=['GET'])
@teacher_required
def get_enrollment_requests():
    """Get all pending enrollment requests for teacher's courses"""
    try:
        teacher_id = session['user_id']

        # Get all pending enrollment requests for this teacher's courses
        requests = enrollment_model.get_pending_requests_by_teacher(teacher_id, course_model)

        requests_list = []
        for req in requests:
            student = user_model.find_by_id(str(req['student_id']))

            requests_list.append({
                "id": str(req['_id']),
                "status": req['status'],
                "created_at": req['created_at'].isoformat(),
                "student": {
                    "id": str(student['_id']),
                    "name": student['name'],
                    "email": student['email']
                } if student else None,
                "course": {
                    "id": str(req['course']['_id']),
                    "course_code": req['course']['course_code'],
                    "course_name": req['course']['course_name']
                }
            })

        return jsonify({"requests": requests_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch enrollment requests: {str(e)}"}), 500


@teacher_bp.route('/enrollment-requests/<request_id>/approve', methods=['POST'])
@teacher_required
def approve_enrollment(request_id):
    """
    Approve an enrollment request

    URL Parameter:
        request_id: ID of the enrollment request to approve
    """
    try:
        teacher_id = session['user_id']

        # Get the enrollment request
        enrollment_request = enrollment_model.find_by_id(request_id)
        if not enrollment_request:
            return jsonify({"error": "Enrollment request not found"}), 404

        # Verify that the teacher owns the course
        course = course_model.find_by_id(str(enrollment_request['course_id']))
        if not course or str(course['teacher_id']) != teacher_id:
            return jsonify({"error": "Unauthorized - not your course"}), 403

        # Approve the enrollment
        success = enrollment_model.update_status(request_id, "approved", user_model)

        if not success:
            return jsonify({"error": "Failed to approve enrollment"}), 500

        # Also update course's student list
        course_model.enroll_student(str(enrollment_request['course_id']), str(enrollment_request['student_id']))

        return jsonify({"message": "Enrollment approved successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to approve enrollment: {str(e)}"}), 500


@teacher_bp.route('/enrollment-requests/<request_id>/reject', methods=['POST'])
@teacher_required
def reject_enrollment(request_id):
    """
    Reject an enrollment request

    URL Parameter:
        request_id: ID of the enrollment request to reject
    """
    try:
        teacher_id = session['user_id']

        # Get the enrollment request
        enrollment_request = enrollment_model.find_by_id(request_id)
        if not enrollment_request:
            return jsonify({"error": "Enrollment request not found"}), 404

        # Verify that the teacher owns the course
        course = course_model.find_by_id(str(enrollment_request['course_id']))
        if not course or str(course['teacher_id']) != teacher_id:
            return jsonify({"error": "Unauthorized - not your course"}), 403

        # Reject the enrollment
        success = enrollment_model.update_status(request_id, "rejected")

        if not success:
            return jsonify({"error": "Failed to reject enrollment"}), 500

        return jsonify({"message": "Enrollment rejected"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to reject enrollment: {str(e)}"}), 500
