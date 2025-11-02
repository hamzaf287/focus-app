"""
Focus Detection App - Main Application
Backend foundation with Flask + MongoDB
"""

from flask import Flask, jsonify, render_template, session, redirect, url_for, Response
from flask_pymongo import PyMongo
from config import config
import os
import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
import time
import threading
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize MongoDB
mongo = PyMongo(app)
db = mongo.db

# Initialize configuration (create folders, etc.)
config[env].init_app(app)


# ==================== AI Model Setup ====================
MODEL_PATH = "focus_binary_classifier_finetuned.pth"
device = torch.device("cpu")

# Load ResNet18 model
model = models.resnet18(weights=None)
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 2)

try:
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()
    print("AI Model loaded successfully.")
except Exception as e:
    print(f"Could not load model: {e}")
    model = None

# Image transformation for model input
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Focus detection globals (per-session storage)
active_sessions = {}  # session_id -> {camera, is_running, focused_frames, distracted_frames, total_frames, start_time}


# ==================== Register Blueprints ====================
from routes import auth_routes, admin_routes, teacher_routes, student_routes

# Initialize routes with database
auth_routes.init_routes(db)
admin_routes.init_routes(db)
teacher_routes.init_routes(db)
student_routes.init_routes(db)

# Register blueprints
app.register_blueprint(auth_routes.auth_bp)
app.register_blueprint(admin_routes.admin_bp)
app.register_blueprint(teacher_routes.teacher_bp)
app.register_blueprint(student_routes.student_bp)


# ==================== Template Routes ====================
@app.route('/')
def home():
    """Home route - redirect to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')


@app.route('/register')
def register_page():
    """Register page"""
    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard - route to correct dashboard based on role"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    role = session.get('user_role')

    if role == 'student':
        return render_template('student_dashboard.html')
    elif role == 'teacher':
        return render_template('teacher_dashboard.html')
    elif role == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('login_page'))


# ==================== Focus Detection Functions ====================
def analyze_frame(frame):
    """Analyze a video frame and return focus status"""
    if model is None:
        return "Unknown"

    img = transform(frame).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img)
        probs = torch.softmax(outputs, dim=1)[0]
        return "Focused" if probs[1] > probs[0] else "Distracted"


def generate_frames(session_id):
    """Generate video frames with focus detection"""
    session_data = active_sessions.get(session_id)
    if not session_data:
        return

    while session_data['is_running']:
        camera = session_data['camera']
        if camera is None:
            break

        success, frame = camera.read()
        if not success:
            break

        status = analyze_frame(frame)
        session_data['total_frames'] += 1

        if status == "Focused":
            session_data['focused_frames'] += 1
        elif status == "Distracted":
            session_data['distracted_frames'] += 1

        # Overlay prediction text on video
        color = (0, 255, 0) if status == "Focused" else (0, 0, 255)
        cv2.putText(frame, f"Status: {status}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# ==================== Focus Detection Routes ====================
@app.route('/session/<session_id>/join')
def join_focus_session(session_id):
    """Render focus detection page for a session"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    return render_template('focus_session.html', session_id=session_id)


@app.route('/session/<session_id>/start', methods=['POST'])
def start_focus_detection(session_id):
    """Start focus detection for a session"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Check if session already running
    if session_id in active_sessions:
        return jsonify({"error": "Session already active"}), 409

    # Initialize camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return jsonify({"error": "Could not access camera"}), 500

    # Store session data
    active_sessions[session_id] = {
        'camera': camera,
        'is_running': True,
        'focused_frames': 0,
        'distracted_frames': 0,
        'total_frames': 0,
        'start_time': time.time(),
        'student_id': session['user_id']
    }

    return jsonify({"status": "Focus detection started", "session_id": session_id})


@app.route('/session/<session_id>/video_feed')
def video_feed(session_id):
    """Video streaming route"""
    return Response(generate_frames(session_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/session/<session_id>/stop', methods=['POST'])
def stop_focus_detection(session_id):
    """Stop focus detection and save report"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    session_data = active_sessions.get(session_id)
    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    # Stop the session
    session_data['is_running'] = False
    if session_data['camera']:
        session_data['camera'].release()

    # Calculate statistics
    duration = int(time.time() - session_data['start_time'])
    total_frames = session_data['total_frames']
    focused_frames = session_data['focused_frames']
    distracted_frames = session_data['distracted_frames']
    focus_percentage = (focused_frames / total_frames * 100) if total_frames else 0

    # Get session and course info from database
    from models.session_model import Session
    from models.course_model import Course
    from models.report_model import FocusReport

    session_model = Session(db)
    course_model = Course(db)
    report_model = FocusReport(db)

    session_obj = session_model.find_by_id(session_id)
    if session_obj:
        course = course_model.find_by_id(session_obj['course_id'])

        # Save report to database
        report = report_model.create_report(
            student_id=session['user_id'],
            course_id=session_obj['course_id'],
            session_id=session_id,
            focus_percentage=focus_percentage,
            focused_frames=focused_frames,
            distracted_frames=distracted_frames,
            total_frames=total_frames,
            duration=duration
        )

    # Clean up
    del active_sessions[session_id]

    return jsonify({
        "status": "Session stopped",
        "statistics": {
            "focus_percentage": round(focus_percentage, 2),
            "total_frames": total_frames,
            "focused_frames": focused_frames,
            "distracted_frames": distracted_frames,
            "duration": duration
        }
    })


# ==================== Report Routes ====================
@app.route('/reports/student/<student_id>')
def get_student_reports(student_id):
    """Get all reports for a student with course and session details"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Ensure user can only access their own reports (unless admin)
    if session['user_id'] != student_id and session.get('user_role') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    from models.report_model import FocusReport
    from models.course_model import Course
    from models.session_model import Session
    from models.user_model import User

    report_model = FocusReport(db)
    course_model = Course(db)
    session_model = Session(db)
    user_model = User(db)

    # Get all reports for student
    reports = report_model.get_reports_by_student(student_id)

    # Enrich reports with course and session details
    enriched_reports = []
    for report in reports:
        course = course_model.find_by_id(str(report['course_id']))
        session_obj = session_model.find_by_id(str(report['session_id']))

        enriched_reports.append({
            'id': str(report['_id']),
            'focus_percentage': report['focus_percentage'],
            'focused_frames': report['focused_frames'],
            'distracted_frames': report['distracted_frames'],
            'total_frames': report['total_frames'],
            'duration': report['duration'],
            'created_at': report['created_at'].isoformat(),
            'report_path': report.get('report_path'),
            'course': {
                'id': str(course['_id']),
                'course_code': course['course_code'],
                'course_name': course['course_name']
            } if course else None,
            'session': {
                'id': str(session_obj['_id']),
                'session_name': session_obj['session_name']
            } if session_obj else None
        })

    return jsonify({"reports": enriched_reports})


@app.route('/reports/teacher/<teacher_id>')
def get_teacher_reports(teacher_id):
    """Get all session reports for a teacher's courses"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    # Ensure user can only access their own reports (unless admin)
    if session['user_id'] != teacher_id and session.get('user_role') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    from models.course_model import Course
    from models.session_model import Session as SessionModel
    from models.report_model import FocusReport
    from models.user_model import User

    course_model = Course(db)
    session_model = SessionModel(db)
    report_model = FocusReport(db)
    user_model = User(db)

    # Get all courses taught by this teacher
    courses = course_model.get_courses_by_teacher(teacher_id)

    all_reports = []
    for course in courses:
        # Get all sessions for this course
        sessions = session_model.get_sessions_by_course(str(course['_id']))

        for session_obj in sessions:
            # Get all reports for this session
            reports = report_model.get_reports_by_session(str(session_obj['_id']))

            for report in reports:
                student = user_model.find_by_id(str(report['student_id']))

                all_reports.append({
                    'id': str(report['_id']),
                    'focus_percentage': report['focus_percentage'],
                    'focused_frames': report['focused_frames'],
                    'distracted_frames': report['distracted_frames'],
                    'total_frames': report['total_frames'],
                    'duration': report['duration'],
                    'created_at': report['created_at'].isoformat(),
                    'report_path': report.get('report_path'),
                    'course': {
                        'id': str(course['_id']),
                        'course_code': course['course_code'],
                        'course_name': course['course_name']
                    },
                    'session': {
                        'id': str(session_obj['_id']),
                        'session_name': session_obj['session_name']
                    },
                    'student': {
                        'id': str(student['_id']),
                        'name': student['name'],
                        'email': student['email']
                    } if student else None
                })

    # Sort by created_at descending
    all_reports.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify({"reports": all_reports})


@app.route('/reports/<report_id>/generate-pdf', methods=['POST'])
def generate_pdf_report(report_id):
    """Generate PDF report for a specific report ID"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401

    from models.report_model import FocusReport
    from models.course_model import Course
    from models.session_model import Session as SessionModel
    from models.user_model import User

    report_model = FocusReport(db)
    course_model = Course(db)
    session_model = SessionModel(db)
    user_model = User(db)

    # Get report
    report = report_model.find_by_id(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404

    # Get related data
    student = user_model.find_by_id(str(report['student_id']))
    course = course_model.find_by_id(str(report['course_id']))
    session_obj = session_model.find_by_id(str(report['session_id']))

    if not student or not course or not session_obj:
        return jsonify({"error": "Related data not found"}), 404

    # Generate PDF
    pdf_filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(app.config['REPORTS_FOLDER'], pdf_filename)

    # Ensure reports directory exists
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

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
        ['Total Frames Analyzed:', str(report['total_frames']), '']
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
    relative_path = f"/static/reports/{pdf_filename}"
    report_model.update_report_path(report_id, relative_path)

    return jsonify({
        "status": "PDF generated successfully",
        "pdf_url": relative_path,
        "filename": pdf_filename
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.command('ping')
        db_status = "Connected"
    except Exception as e:
        db_status = f"Disconnected: {str(e)}"

    return jsonify({
        "status": "running",
        "database": db_status
    }), 200


# ==================== Error Handlers ====================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return jsonify({"error": "Forbidden"}), 403


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 errors"""
    return jsonify({"error": "Unauthorized"}), 401


# ==================== Run App ====================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'

    print("\n" + "="*50)
    print("Focus Detection App Starting...")
    print(f"Environment: {env}")
    print(f"Port: {port}")
    print(f"Debug Mode: {debug}")
    print(f"MongoDB URI: {app.config['MONGO_URI']}")
    print("="*50 + "\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
