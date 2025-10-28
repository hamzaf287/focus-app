import cv2
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for, send_file
from functools import wraps
import time
import threading
import pygetwindow as gw
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime

# ---------------- Flask Setup ----------------
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this to a random secret key

# ---------------- Sample Users ----------------
USERS = {
    'student': 'focus123',
    'admin': 'admin123',
    'demo': 'demo123'
}

# ---------------- Model Definition ----------------
class FocusModel(nn.Module):
    def __init__(self):
        super(FocusModel, self).__init__()
        self.resnet = models.resnet18(weights=None)
        num_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_features, 2)

    def forward(self, x):
        return self.resnet(x)

# ---------------- Load Model ----------------
MODEL_PATH = "focus_binary_classifier_finetuned.pth"
device = torch.device("cpu")

# Load the model directly as ResNet18 with modified final layer
model = models.resnet18(weights=None)
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, 2)

try:
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"⚠️ Could not load model: {e}")
    model = None

# ---------------- Globals ----------------
camera = None
is_running = False
focused_frames = 0
distracted_frames = 0
total_frames = 0
session_start_time = None
tab_switches = []
last_report_data = None  # Store last session data for PDF generation
current_course = None  # Store selected course for the session
session_history = {}  # Store all session reports per user (username -> list of reports)

# ---------------- Screen Activity Monitor ----------------
def monitor_screen_activity():
    global tab_switches
    last_active = ""
    while is_running:
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                title = active_window.title
                if title != last_active:
                    last_active = title
                    tab_switches.append((time.strftime("%H:%M:%S"), title))
            time.sleep(1)
        except Exception:
            continue

# ---------------- Frame Analysis ----------------
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

def analyze_frame(frame):
    if model is None:
        return "Unknown"

    img = transform(frame).unsqueeze(0)

    with torch.no_grad():
        outputs = model(img)
        probs = torch.softmax(outputs, dim=1)[0]
        print("🔍 Model output probabilities:", probs.tolist())  # Debug line

        # Adjust based on your model’s output ordering
        return "Focused" if probs[1] > probs[0] else "Distracted"

# ---------------- Video Generator ----------------
def generate_frames():
    global focused_frames, distracted_frames, total_frames
    while is_running:
        if camera is None:
            break
        success, frame = camera.read()
        if not success:
            print("⚠️ Failed to read frame from camera")
            break

        status = analyze_frame(frame)
        total_frames += 1
        if status == "Focused":
            focused_frames += 1
        elif status == "Distracted":
            distracted_frames += 1

        # Overlay prediction text on video
        cv2.putText(frame, f"Status: {status}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if status == "Focused" else (0, 0, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ---------------- Authentication Decorator ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- Routes ----------------
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST request - handle login
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in USERS and USERS[username] == password:
        session['username'] = username
        return jsonify({'status': 'success', 'message': 'Login successful'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    courses = ["CSCS460ASP2024", "COMP451BSP2024", "COMP301ASP2024"]
    return render_template('index.html', courses=courses, username=session.get('username'))

@app.route('/history')
@login_required
def history():
    return render_template('history.html', username=session.get('username'))

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html', username=session.get('username'))

@app.route('/get_session_history')
@login_required
def get_session_history():
    """Return session history for the current user"""
    username = session.get('username', 'User')
    user_sessions = session_history.get(username, [])
    # Return sessions in reverse order (newest first)
    return jsonify({"sessions": list(reversed(user_sessions))})

@app.route('/start', methods=['POST'])
@login_required
def start_focus():
    global is_running, focused_frames, distracted_frames, total_frames, session_start_time, tab_switches, camera, current_course

    # Get selected course from request
    data = request.get_json() if request.is_json else {}
    current_course = data.get('course', 'Not specified')

    # Initialize camera when session starts
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return jsonify({"status": "Error: Could not access camera"}), 500

    is_running = True
    focused_frames = distracted_frames = total_frames = 0
    tab_switches = []
    session_start_time = time.time()

    threading.Thread(target=monitor_screen_activity, daemon=True).start()
    return jsonify({"status": "Session started", "course": current_course})

@app.route('/stop', methods=['POST'])
@login_required
def stop_focus():
    global is_running, camera, last_report_data, session_history
    is_running = False

    # Release camera when session stops
    if camera is not None:
        camera.release()
        camera = None
    duration = time.time() - session_start_time
    focus_percentage = (focused_frames / total_frames * 100) if total_frames else 0

    report = (
        "===== Focus Report =====\n"
        f"Course: {current_course or 'Not specified'}\n"
        f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Session Duration: {int(duration)} seconds\n"
        f"Total Frames: {total_frames}\n"
        f"Focused: {focused_frames}\n"
        f"Distracted: {distracted_frames}\n"
        f"Focus %: {focus_percentage:.2f}%\n"
        "\n--- Tab Switches ---\n"
    )

    if tab_switches:
        for t, title in tab_switches:
            report += f"[{t}] {title}\n"
    else:
        report += "No tab switches detected.\n"

    # Store report data for PDF generation
    report_data = {
        "id": int(time.time() * 1000),  # Unique ID using timestamp
        "username": session.get('username', 'User'),
        "course": current_course or 'Not specified',
        "date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "duration": int(duration),
        "total_frames": total_frames,
        "focused_frames": focused_frames,
        "distracted_frames": distracted_frames,
        "focus_percentage": round(focus_percentage, 2),
        "tab_switches": list(tab_switches)  # Copy the list
    }

    last_report_data = report_data

    # Add to session history
    username = session.get('username', 'User')
    if username not in session_history:
        session_history[username] = []
    session_history[username].append(report_data)

    print(report)
    return jsonify({
        "status": "Session stopped",
        "report": report,
        "stats": {
            "focus_percentage": round(focus_percentage, 2),
            "total_frames": total_frames,
            "focused_frames": focused_frames,
            "distracted_frames": distracted_frames,
            "duration": int(duration)
        }
    })

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/live_stats')
@login_required
def live_stats():
    """Return current session stats for real-time updates"""
    focus_percentage = (focused_frames / total_frames * 100) if total_frames else 0
    return jsonify({
        "focus_percentage": round(focus_percentage, 2),
        "total_frames": total_frames,
        "focused_frames": focused_frames,
        "distracted_frames": distracted_frames,
        "is_running": is_running
    })

@app.route('/download_report_pdf')
@login_required
def download_report_pdf():
    """Generate and download focus report as PDF"""
    if last_report_data is None:
        return jsonify({"error": "No report data available"}), 404

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Title
    title = Paragraph("FOCUS CHECK - Session Report", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3 * inch))

    # User info
    user_info = f"<b>Student:</b> {last_report_data['username']}<br/><b>Course:</b> {last_report_data['course']}<br/><b>Date:</b> {last_report_data['date']}"
    story.append(Paragraph(user_info, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Session Summary
    story.append(Paragraph("Session Summary", heading_style))

    # Stats table
    stats_data = [
        ['Metric', 'Value'],
        ['Course', last_report_data['course']],
        ['Session Duration', f"{last_report_data['duration']} seconds"],
        ['Total Frames Analyzed', str(last_report_data['total_frames'])],
        ['Focused Frames', str(last_report_data['focused_frames'])],
        ['Distracted Frames', str(last_report_data['distracted_frames'])],
        ['Focus Percentage', f"{last_report_data['focus_percentage']}%"]
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(stats_table)
    story.append(Spacer(1, 0.4 * inch))

    # Tab Switches
    story.append(Paragraph("Tab/Window Activity", heading_style))

    if last_report_data['tab_switches']:
        tab_data = [['Time', 'Window/Tab Title']]
        for t, title in last_report_data['tab_switches']:
            tab_data.append([t, title])

        tab_table = Table(tab_data, colWidths=[1.5*inch, 4.5*inch])
        tab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tab_table)
    else:
        story.append(Paragraph("No tab switches detected during this session.", styles['Normal']))

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    footer_text = f"<i>Generated by Focus Check on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    story.append(Paragraph(footer_text, styles['Normal']))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    # Generate filename
    filename = f"focus_report_{last_report_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route('/download_session_pdf/<int:session_id>')
@login_required
def download_session_pdf(session_id):
    """Generate and download PDF for a specific session from history"""
    username = session.get('username', 'User')
    user_sessions = session_history.get(username, [])

    # Find the session by ID
    report_data = None
    for s in user_sessions:
        if s['id'] == session_id:
            report_data = s
            break

    if report_data is None:
        return jsonify({"error": "Session not found"}), 404

    # Create PDF in memory (reuse same PDF generation logic)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Title
    title = Paragraph("FOCUS CHECK - Session Report", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3 * inch))

    # User info
    user_info = f"<b>Student:</b> {report_data['username']}<br/><b>Course:</b> {report_data['course']}<br/><b>Date:</b> {report_data['date']}"
    story.append(Paragraph(user_info, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Session Summary
    story.append(Paragraph("Session Summary", heading_style))

    # Stats table
    stats_data = [
        ['Metric', 'Value'],
        ['Course', report_data['course']],
        ['Session Duration', f"{report_data['duration']} seconds"],
        ['Total Frames Analyzed', str(report_data['total_frames'])],
        ['Focused Frames', str(report_data['focused_frames'])],
        ['Distracted Frames', str(report_data['distracted_frames'])],
        ['Focus Percentage', f"{report_data['focus_percentage']}%"]
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(stats_table)
    story.append(Spacer(1, 0.4 * inch))

    # Tab Switches
    story.append(Paragraph("Tab/Window Activity", heading_style))

    if report_data['tab_switches']:
        tab_data = [['Time', 'Window/Tab Title']]
        for t, title in report_data['tab_switches']:
            tab_data.append([t, title])

        tab_table = Table(tab_data, colWidths=[1.5*inch, 4.5*inch])
        tab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(tab_table)
    else:
        story.append(Paragraph("No tab switches detected during this session.", styles['Normal']))

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    footer_text = f"<i>Generated by Focus Check on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    story.append(Paragraph(footer_text, styles['Normal']))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    # Generate filename
    filename = f"focus_report_{report_data['username']}_{report_data['course']}_{session_id}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

# ---------------- Main ----------------
if __name__ == "__main__":
    app.run(debug=True)
