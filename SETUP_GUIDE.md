# FocusCheck - Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning)

## Step-by-Step Setup Instructions

### 1. Install Python Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

If you get permission errors, use:

```bash
pip install --user -r requirements.txt
```

### 2. Download the AI Model

The focus detection model is required but not included in the repository due to its large size.

**Download the model file:**

- Model: `focus_binary_classifier_finetuned.pth`
- Place it in the root directory: `focus_app/focus_binary_classifier_finetuned.pth`

**Model download options:**

1. Ask your partner to share the model file directly
2. Download from the original source (if available)
3. Or contact the project owner for the model file

**⚠️ CRITICAL:** Without this file, the application will fail to start with a 500 server error!

### 3. Create Required Directories

The application needs these directories to store generated files:

```bash
mkdir -p static/videos
mkdir -p static/reports
```

On Windows:

```cmd
mkdir static\videos
mkdir static\reports
```

### 4. Database Configuration

The application uses MongoDB Atlas (cloud database). The connection string is already configured in `app.py`:

```python
mongodb+srv://hamzafaisal18_db_user:***@focuscheckcluster.zswpzmd.mongodb.net/focus_app
```

**You're sharing the same database**, so all users, courses, and data are synchronized.

### 5. Run the Application

```bash
python app.py
```

The server will start on `http://127.0.0.1:5000` or `http://localhost:5000`

### 6. Access the Application

Open your web browser and navigate to:

```
http://localhost:5000
```

## Login Credentials

Since you're sharing the same database, use any existing account credentials:

**Admin Account:**

- Email: admin@focuscheck.com (or your admin email)
- Password: [your admin password]

**Test Accounts:**

- Use any existing student/teacher accounts from the shared database

**Create New Account:**

- Go to `/register` to create a new account
- Students can register directly
- Teachers need admin approval after registration

## Common Issues & Solutions

### Quick Diagnostic Guide

**If you're getting 500 errors, check the terminal output:**

| Terminal Error Message | Issue | Jump to |
|------------------------|-------|---------|
| `ModuleNotFoundError: No module named 'flask'` | Missing dependencies | Issue 1 |
| `FileNotFoundError: focus_binary_classifier_finetuned.pth` | Missing AI model | Issue 2 |
| `ServerSelectionTimeoutError` or `No servers found yet` | **MongoDB IP blocked** | **Issue 3** ⚠️ |
| `OSError: [Errno 98] Address already in use` | Port conflict | Issue 4 |
| No error in terminal, just browser shows 500 | Check all of the above | - |

### Issue 1: "Module not found" errors

**Solution:** Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install Flask flask-pymongo pymongo bcrypt python-dateutil python-dotenv torch torchvision opencv-python reportlab pygetwindow Pillow
```

### Issue 2: "Model file not found" or "500 Server Error on Login"

**Solution:** Ensure `focus_binary_classifier_finetuned.pth` exists in the root directory:

```
focus_app/
├── focus_binary_classifier_finetuned.pth  ← Must be here
├── app.py
├── requirements.txt
└── ...
```

**To verify the model file exists:**

- Windows: `dir focus_binary_classifier_finetuned.pth`
- Linux/Mac: `ls -lh focus_binary_classifier_finetuned.pth`

If missing, get it from your partner who has the working setup!

### Issue 3: Cannot connect to database / "ServerSelectionTimeoutError"

**⚠️ THIS IS THE MOST COMMON CAUSE OF 500 ERRORS!**

When your partner runs the app and gets 500 errors, it's usually because their IP address is blocked by MongoDB Atlas.

**Solution - Add IP to MongoDB Atlas Whitelist:**

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Log in with account: `hamzafaisal18_db_user` (ask project owner for password)
3. Select your cluster: **focuscheckCluster**
4. Click **"Network Access"** (under Security in left sidebar)
5. Click **"+ ADD IP ADDRESS"** button
6. Choose ONE option:
   - **Option A (Recommended for team):** Click **"ALLOW ACCESS FROM ANYWHERE"**
     - Enter: `0.0.0.0/0`
     - This allows all team members to connect
     - Less secure but easier for development
   - **Option B (More secure):** Click **"ADD CURRENT IP ADDRESS"**
     - Each team member needs to add their own IP
     - More secure but requires updates when IP changes
7. Click **"Confirm"**
8. **Wait 1-2 minutes** for changes to take effect
9. Try running the app again

**How to identify this issue:**
- Terminal shows: `pymongo.errors.ServerSelectionTimeoutError`
- Or: `No servers found yet`
- Or: App hangs for 30 seconds then shows 500 error
- Or: `MongoClient` connection timeout

**Quick fix:** If you have MongoDB Atlas access, set IP whitelist to `0.0.0.0/0` to allow all IPs

### Issue 4: Port 5000 already in use

**Solution:** Either:

1. Stop the process using port 5000
2. Or change the port in `app.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Changed to 5001
```

### Issue 5: Camera not working

**Solution:**

- Grant browser permission to access camera
- Make sure your camera is not being used by another application
- Try a different browser (Chrome/Edge recommended)

### Issue 6: Login not working

**Possible causes:**

1. **Wrong credentials** - Try the "Forgot Password" link or create a new account
2. **Database connection issue** - Check console for MongoDB errors
3. **Session issues** - Clear browser cookies/cache

**Debug steps:**

1. Check the terminal where `app.py` is running for error messages
2. Look for lines like:
   ```
   [timestamp] "POST /auth/login HTTP/1.1" 200  ← Success
   [timestamp] "POST /auth/login HTTP/1.1" 401  ← Wrong credentials
   [timestamp] "POST /auth/login HTTP/1.1" 500  ← Server error
   ```
3. If you see 401: Credentials are wrong
4. If you see 500: Check terminal for Python error traceback

## Project Structure

```
focus_app/
├── focus_binary_classifier_finetuned.pth  # AI model (REQUIRED - must get from partner)
├── app.py                       # Main application
├── requirements.txt             # Dependencies
├── models/                      # Database models
│   ├── user_model.py
│   ├── course_model.py
│   └── ...
├── routes/                      # API routes
│   ├── auth_routes.py
│   ├── student_routes.py
│   ├── teacher_routes.py
│   └── admin_routes.py
├── templates/                   # HTML templates
├── static/                      # Static files
│   ├── css/
│   ├── videos/                 # Generated session videos
│   └── reports/                # Generated PDF reports
└── utils/                      # Utility functions
```

## Testing the Setup

1. **Start the server:**

   ```bash
   python app.py
   ```

2. **You should see:**

   ```
   AI Model loaded successfully.
   ==================================================
   Focus Detection App Starting...
   Environment: development
   Port: 5000
   Debug Mode: True
   ==================================================
   * Running on http://127.0.0.1:5000
   ```

3. **Open browser and test:**
   - Go to `http://localhost:5000`
   - You should see the login page
   - Try logging in with existing credentials

## Need Help?

If you encounter issues:

1. **Check the terminal output** for error messages
2. **Verify all dependencies** are installed: `pip list`
3. **Confirm the model file** exists:
   - Linux/Mac: `ls -lh focus_binary_classifier_finetuned.pth`
   - Windows: `dir focus_binary_classifier_finetuned.pth`
4. **Test database connection** - look for MongoDB connection messages in terminal
5. **Contact the project owner** with:
   - Error message from terminal
   - Steps you followed
   - Your Python version: `python --version`

## Development Notes

- **Debug Mode:** Currently enabled (shows detailed errors)
- **Auto-reload:** Server restarts automatically when code changes
- **Database:** Shared MongoDB Atlas instance (all developers see same data)
- **AI Model:** Required for focus detection during sessions
- **Reports:** Generated in `static/reports/` (ignored by git)
- **Videos:** Saved in `static/videos/` (ignored by git)

## Security Notes

⚠️ **Important:**

- The MongoDB credentials are hardcoded in `app.py`
- In production, use environment variables
- Don't commit sensitive data to public repositories
- Change default admin password after first login

## Next Steps

After successful setup:

1. **Login** with existing credentials or create a new account
2. **Explore** the different dashboards (Student/Teacher/Admin)
3. **Test** creating a session and joining it
4. **Check** if focus detection and report generation work

---

**Last Updated:** November 2025
**Version:** 1.0
**Support:** Contact project owner for assistance
