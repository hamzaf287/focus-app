# FocusCheck - AI-Powered Focus Tracking Application

A comprehensive webcam-based focus tracking application with role-based access control (Admin, Teacher, Student) that uses machine learning to monitor student concentration during study sessions. Built with Flask, MongoDB, PyTorch, and OpenCV.

![FocusCheck](static/Favicon.svg)

---

## Features

### For Students
- 🎥 **Real-time Focus Detection** - Live camera feed with AI-powered focus tracking
- 📊 **Personal Analytics** - View focus statistics and trends
- 📚 **Course Enrollment** - Request enrollment in courses (requires teacher approval)
- 📝 **Session History** - Track all past focus sessions with detailed reports
- 📄 **PDF Reports** - Download session reports with focus analysis

### For Teachers
- 👨‍🏫 **Course Management** - Create and manage courses
- 📹 **Session Creation** - Start focus detection sessions for courses
- ✅ **Enrollment Approval** - Approve/reject student enrollment requests
- 📊 **Class Analytics** - View aggregate focus data for courses
- 📈 **Student Reports** - Monitor individual and class performance

### For Admins
- 👤 **User Management** - View all users (students, teachers)
- ✅ **Teacher Approval** - Approve new teacher registrations
- 📚 **Course Oversight** - Manage all courses in the system
- 📊 **System Statistics** - Dashboard with system-wide metrics

---

## Technologies Used

### Backend
- **Flask 3.0.0** - Web framework with Blueprint architecture
- **MongoDB Atlas** - Cloud database (PyMongo driver)
- **PyTorch** - Deep learning framework for focus detection
- **OpenCV (cv2)** - Computer vision and webcam handling
- **ReportLab** - PDF generation
- **bcrypt** - Password hashing

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript (Vanilla)** - Interactive dashboard components
- **Remix Icons** - Icon library

### Machine Learning
- **ResNet18** - Fine-tuned for binary classification (focused/distracted)
- **Real-time inference** - Frame-by-frame analysis during sessions

---

## Architecture

### Role-Based Access Control

**Admin:**
- Approve/reject teacher registrations
- View system statistics
- Manage courses (create, delete, assign teachers)

**Teacher:**
- Must be approved by admin before creating courses/sessions
- Create courses and focus detection sessions
- Approve/reject student enrollment requests
- View reports for their courses

**Student:**
- Request enrollment in courses
- Join active focus detection sessions
- View personal focus reports and statistics

### Approval Workflows

1. **Teacher Approval:** Teacher registers → Admin approves → Teacher can create courses/sessions
2. **Student Enrollment:** Student requests enrollment → Teacher approves → Student can join sessions

---

## Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (or local MongoDB instance)
- Webcam/Camera device
- Modern web browser (Chrome, Firefox, Edge, Safari)

---

## Installation

These steps are written so you can follow them even if you are not a programmer.

### 1. Install the tools you need

You only need to do this once on a computer.

- **Python 3.8 or higher**
  - Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
  - During installation on Windows, make sure “Add Python to PATH” is checked.
- **Node.js (for the frontend)**
  - Download from [https://nodejs.org](https://nodejs.org) (LTS version is fine).
- **Git (to download this project)**
  - Download from [https://git-scm.com/downloads](https://git-scm.com/downloads)

### 2. Download the project

Open a terminal / command prompt and run:

```bash
git clone <repository-url>
cd focus_app
```

### 3. Set up the backend (Flask API)

1. Go into the backend folder:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure MongoDB (database):
   - Open `backend/config.py` in a text editor.
   - Find the `MONGO_URI` setting.
   - If you already have a MongoDB connection string, paste it there.
   - Otherwise, you can leave the existing value and use the same database that was used during development.

5. Start the backend server:

   ```bash
   python app.py
   ```

   - The backend will start on: `http://localhost:5000`
   - Leave this window open while you use the app.

### 4. Set up the frontend (React UI)

Open a **new** terminal / command prompt (do not close the backend one) and:

1. Go into the frontend folder:
   ```bash
   cd focus_app/frontend
   ```

2. Install JavaScript dependencies (this may take a few minutes the first time):

   ```bash
   npm install
   ```

3. Start the frontend development server:

   ```bash
   npm run dev
   ```

   - The frontend will tell you a URL, usually: `http://localhost:5173`
   - Open that URL in your browser.
   - The frontend is already configured to talk to the backend at `http://localhost:5000`.

### 5. Logging in and using the app

Once both servers are running:

1. Open the frontend URL in your browser (for example `http://localhost:5173`).
2. Use the **Register** page to create:
   - A **student** account for testing student features.
   - A **teacher** account (will need admin approval).
3. To create an **admin** account, you may need to insert one directly in the database or use a preconfigured admin if one exists in your environment.
4. As admin, approve teacher accounts and create courses, then log in as teacher and student to try the full workflow.

---

## Project Structure

```
focus_app/
│
├── app.py                           # Main Flask application
├── config.py                        # Configuration (MongoDB, secrets)
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── docs/                            # Testing & documentation
│   ├── WORKFLOW_VERIFICATION_REPORT.md   # Complete verification report
│   ├── simple_test.py               # End-to-end automated tests
│   ├── test_approval_workflows.py   # Comprehensive test suite
│   ├── verify_db_data.py            # MongoDB consistency checker
│   └── manual_test.md               # Manual testing guide
│
├── models/                          # Database models
│   ├── user_model.py                # User model (students, teachers, admins)
│   ├── course_model.py              # Course model
│   ├── session_model.py             # Focus session model
│   ├── report_model.py              # Focus report model
│   └── enrollment_model.py          # Enrollment request model
│
├── routes/                          # API endpoints
│   ├── auth_routes.py               # Authentication (login, register, logout)
│   ├── student_routes.py            # Student endpoints
│   ├── teacher_routes.py            # Teacher endpoints
│   └── admin_routes.py              # Admin endpoints
│
├── static/                          # Static assets
│   ├── videos/                      # Video recordings
│   ├── reports/                     # Generated PDF reports
│   └── Favicon.svg                  # App icon
│
└── templates/                       # HTML templates
    ├── index.html                   # Landing page
    ├── login.html                   # Login page
    ├── register.html                # Registration page
    ├── student_dashboard.html       # Student dashboard
    ├── teacher_dashboard.html       # Teacher dashboard
    └── admin_dashboard.html         # Admin dashboard
```

---

## Default Accounts

### Admin Account
Create an admin account using registration or directly in MongoDB:

```python
# Example: Register via API
{
  "name": "Admin User",
  "email": "admin@focuscheck.com",
  "password": "admin123",  # Change this!
  "role": "admin"
}
```

### First Teacher
Register as teacher, then admin must approve before they can create courses.

### First Student
Register as student, then request enrollment in courses.

**⚠️ Important:** Change default passwords in production!

---

## Testing & Verification

### Run Automated Tests

```bash
# Simple end-to-end test (all 10 steps)
python docs/simple_test.py

# Comprehensive test with detailed output
python docs/test_approval_workflows.py

# Verify database consistency
python docs/verify_db_data.py
```

### Manual Testing

See [docs/manual_test.md](docs/manual_test.md) for curl commands to test all endpoints.

### Verification Report

See [docs/WORKFLOW_VERIFICATION_REPORT.md](docs/WORKFLOW_VERIFICATION_REPORT.md) for complete verification documentation including:
- All issues found and fixed
- Test results
- Database schema validation
- Security verification

---

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user info

### Student Routes (`/student`)
- `GET /courses/available` - List available courses
- `GET /courses/enrolled` - List enrolled courses
- `POST /courses/<id>/enroll` - Request enrollment
- `GET /enrollment-requests` - View enrollment requests
- `GET /sessions/<id>/join` - Join active session
- `GET /reports` - View focus reports
- `GET /statistics` - View personal statistics

### Teacher Routes (`/teacher`)
- `GET /courses` - List teacher's courses
- `POST /sessions` - Create focus detection session
- `GET /sessions` - List teacher's sessions
- `POST /sessions/<id>/end` - End active session
- `GET /enrollment-requests` - View pending requests
- `POST /enrollment-requests/<id>/approve` - Approve enrollment
- `POST /enrollment-requests/<id>/reject` - Reject enrollment
- `GET /reports/course/<id>` - Course reports

### Admin Routes (`/admin`)
- `GET /teachers/pending` - List unapproved teachers
- `POST /teachers/approve/<id>` - Approve teacher
- `POST /teachers/reject/<id>` - Reject teacher
- `POST /courses` - Create course
- `GET /courses` - List all courses
- `DELETE /courses/<id>` - Delete course
- `GET /statistics` - System statistics

---

## User Workflows

### Teacher Workflow
1. Register as teacher
2. Login (can access dashboard but cannot create resources)
3. Wait for admin approval
4. Once approved, create courses
5. Create focus detection sessions for courses
6. Approve student enrollment requests
7. View class and student reports

### Student Workflow
1. Register as student
2. Login and view available courses
3. Request enrollment in desired courses
4. Wait for teacher approval
5. Once approved, join active sessions
6. View personal focus reports and statistics

### Admin Workflow
1. Login as admin
2. View pending teacher registrations
3. Approve/reject teachers
4. Create courses and assign teachers
5. Monitor system statistics

---

## MongoDB Collections

### users
- Students, teachers, and admins
- Fields: `name`, `email`, `password` (hashed), `role`, `approved` (for teachers), `enrolled_courses` (for students)

### courses
- Course information
- Fields: `course_code`, `course_name`, `teacher_id`, `students` (array)

### enrollment_requests
- Student enrollment requests
- Fields: `student_id`, `course_id`, `status` (pending/approved/rejected), `created_at`, `updated_at`

### sessions
- Focus detection sessions
- Fields: `session_name`, `course_id`, `teacher_id`, `start_time`, `end_time`, `status`

### reports
- Focus reports for sessions
- Fields: `session_id`, `student_id`, `course_id`, `focus_percentage`, `focused_frames`, `distracted_frames`, `total_frames`

---

## Configuration

### Environment Variables

```bash
# MongoDB
export MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/focus_app"

# Flask
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="development"  # or "production"
```

### Config File

Edit `config.py`:

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/focus_app'
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
```

---

## Security Features

- ✅ Password hashing with bcrypt
- ✅ Session-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Route protection with decorators
- ✅ Approval workflows (teacher approval, enrollment approval)
- ✅ Input validation
- ✅ CSRF protection ready (add flask-wtf for forms)

---

## Troubleshooting

### MongoDB Connection Error

**Issue:** Cannot connect to MongoDB

**Solutions:**
- Verify MongoDB URI in `config.py`
- Check network connectivity
- Whitelist your IP in MongoDB Atlas
- Verify database user credentials

### Camera Not Working

**Issue:** Camera feed not showing

**Solutions:**
- Ensure webcam is connected
- Check browser permissions - allow camera access
- Try a different browser
- Restart the Flask server

### Teacher Cannot Create Sessions

**Issue:** 403 error when creating sessions

**Solution:** Teacher must be approved by admin first. Check approval status:

```python
# Via API
GET /auth/me
# Response should have: "approved": true
```

### Student Cannot Join Session

**Issue:** Student blocked from joining

**Solution:** Student must be enrolled in the course. Check enrollment status:

```python
# Via API
GET /student/courses/enrolled
# Course should appear in the list
```

---

## Development

### Run in Debug Mode

```python
# app.py
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Testing Locally

Use the provided test scripts in `docs/`:

```bash
# Ensure Flask app is running on localhost:5000
python docs/simple_test.py
```

---

## Production Deployment

1. **Disable Debug Mode**
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Use Environment Variables**
   - Store `MONGO_URI` and `SECRET_KEY` in environment variables
   - Never commit credentials to version control

3. **Use HTTPS**
   - Deploy behind reverse proxy (Nginx, Apache)
   - Use SSL/TLS certificates

4. **Add Rate Limiting**
   - Install flask-limiter
   - Limit login attempts

5. **Change Default Credentials**
   - Update admin password
   - Require strong passwords

---

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

---

## License

This project is open source and available under the MIT License.

---

## Documentation

- [Complete Verification Report](docs/WORKFLOW_VERIFICATION_REPORT.md) - Detailed testing and verification
- [Manual Testing Guide](docs/manual_test.md) - curl commands for all endpoints
- [Test Scripts](docs/) - Automated testing scripts

---

## Support

For issues and questions:
- Check [docs/WORKFLOW_VERIFICATION_REPORT.md](docs/WORKFLOW_VERIFICATION_REPORT.md) for troubleshooting
- Review test scripts in `docs/`
- Open an issue on GitHub

---

**Made with ❤️ for educational institutions**

*Version: 2.0.0 - Production Ready*
*Last Updated: November 2025*
*Status: ✅ All Workflows Verified*
