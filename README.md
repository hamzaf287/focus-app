# Focus Check - AI-Powered Focus Tracking Application

A webcam-based focus tracking application that uses machine learning to monitor student concentration during study sessions. Built with Flask, PyTorch, and OpenCV.

![Focus Check](static/Favicon.svg)

## Features

- 🎥 **Real-time Webcam Monitoring** - Live camera feed with focus detection
- 🧠 **AI-Powered Analysis** - ResNet18-based deep learning model for focus detection
- 📊 **Analytics Dashboard** - Visual charts and statistics of focus patterns
- 📝 **Session History** - Track all past focus sessions with detailed reports
- 📄 **PDF Reports** - Download detailed session reports
- 👤 **User Authentication** - Secure login system with session management
- 📚 **Course Tracking** - Organize sessions by course/subject
- 🎨 **Modern UI** - Clean, responsive interface with gradient themes

## Technologies Used

### Backend
- **Flask** - Web framework
- **PyTorch** - Deep learning framework
- **TorchVision** - Pre-trained models and transformations
- **OpenCV (cv2)** - Computer vision and webcam handling
- **ReportLab** - PDF generation

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript (Vanilla)** - Interactive UI components
- **Chart.js** - Data visualization
- **Remix Icons** - Icon library
- **Font Awesome** - Additional icons

### Machine Learning
- **ResNet18** - Fine-tuned for binary classification (focused/distracted)
- **Real-time inference** - Frame-by-frame analysis

## Prerequisites

- Python 3.8 or higher
- Webcam/Camera device
- Modern web browser (Chrome, Firefox, Edge, Safari)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd focus_app
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install flask
pip install torch torchvision
pip install opencv-python
pip install reportlab
pip install pygetwindow
```

**Or install all at once:**

```bash
pip install flask torch torchvision opencv-python reportlab pygetwindow
```

### 4. Verify Installation

```bash
python -c "import flask, torch, cv2, reportlab; print('All dependencies installed successfully!')"
```

## Project Structure

```
focus_app/
│
├── app.py                      # Main Flask application
├── focus_model.pth             # Pre-trained ML model
├── README.md                   # This file
│
├── static/                     # Static assets
│   ├── Favicon.svg            # App icon
│   ├── script.js              # Dashboard JavaScript
│   └── style.css              # Dashboard styles
│
└── templates/                  # HTML templates
    ├── login.html             # Login page
    ├── index.html             # Dashboard (main page)
    ├── analytics.html         # Analytics page
    └── history.html           # Session history page
```

## Configuration

### Default Users

The application comes with demo user accounts:

| Username | Password    | Role    |
|----------|-------------|---------|
| student  | focus123    | Student |
| admin    | admin123    | Admin   |
| demo     | demo123     | Demo    |

**⚠️ Important:** Change these credentials in production!

### Modify User Credentials

Edit `app.py` line ~15:

```python
USERS = {
    'your_username': 'your_password',
    # Add more users as needed
}
```

### Secret Key

Update the Flask secret key in `app.py` for production:

```python
app.secret_key = 'your-secret-key-change-this-in-production'
```

## Running the Application

### 1. Start the Flask Server

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

### 2. Access the Application

Open your web browser and navigate to:

```
http://localhost:5000
```

### 3. Login

Use one of the demo credentials:
- **Username:** `student`
- **Password:** `focus123`

### 4. Start a Focus Session

1. Select a course from the dropdown
2. Click "Start Session"
3. Allow camera access when prompted
4. The AI will track your focus in real-time
5. Click "Stop Session" when done
6. View your report and download PDF

## Features Guide

### Dashboard
- **Live Camera Feed** - See real-time webcam output
- **Session Controls** - Start/stop focus tracking sessions
- **Live Statistics** - View focus percentage and frame counts
- **Session Timer** - Track session duration
- **Course Selection** - Organize sessions by subject

### Analytics
- **Focus Trend Chart** - Line graph showing focus over time
- **Focus Distribution** - Doughnut chart of focused vs distracted time
- **Study Time Analysis** - Bar chart of time spent per course
- **Performance Table** - Detailed course performance breakdown

### History
- **Session Archive** - All past sessions with timestamps
- **Filter by Course** - View sessions for specific courses
- **Summary Statistics** - Total sessions, duration, average focus
- **PDF Downloads** - Export individual session reports

### Profile Dropdown
- **My Profile** - View user information
- **Settings** - Configure app preferences
- **Help & Support** - Get assistance
- **Logout** - End session securely

## Troubleshooting

### Camera Not Working

**Issue:** Camera feed not showing

**Solutions:**
- Ensure webcam is connected and not in use by another application
- Check browser permissions - allow camera access
- Try a different browser
- Restart the Flask server

### Model Loading Error

**Issue:** `state_dict` key mismatch or model not found

**Solutions:**
- Ensure `focus_model.pth` is in the root directory
- Verify the model file is not corrupted
- Check PyTorch version compatibility

### Port Already in Use

**Issue:** `Address already in use`

**Solutions:**
```bash
# Windows - Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:5000 | xargs kill -9
```

Or change the port in `app.py`:
```python
app.run(debug=True, port=5001)
```

### Import Errors

**Issue:** `ModuleNotFoundError`

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade flask torch torchvision opencv-python reportlab pygetwindow
```

## Development

### Run in Debug Mode

The app runs in debug mode by default:

```python
# app.py (line ~end)
if __name__ == '__main__':
    app.run(debug=True)
```

Debug mode features:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

### Disable Debug for Production

```python
app.run(debug=False, host='0.0.0.0')
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Login page |
| `/login` | POST | Authenticate user |
| `/logout` | GET | End session |
| `/dashboard` | GET | Main dashboard |
| `/analytics` | GET | Analytics page |
| `/history` | GET | Session history |
| `/start` | POST | Start focus session |
| `/stop` | POST | Stop focus session |
| `/video_feed` | GET | MJPEG video stream |
| `/live_stats` | GET | Real-time statistics |
| `/get_session_history` | GET | Fetch all sessions |
| `/download_report_pdf` | GET | Download latest report |
| `/download_session_pdf/<id>` | GET | Download specific report |

## Dependencies Version Info

```
Flask>=2.0.0
torch>=1.9.0
torchvision>=0.10.0
opencv-python>=4.5.0
reportlab>=3.6.0
pygetwindow>=0.0.9
```

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

## Performance Tips

1. **Close Unused Applications** - Free up camera resources
2. **Good Lighting** - Improves model accuracy
3. **Stable Camera Position** - Better tracking consistency
4. **Clear Browser Cache** - If experiencing slow performance

## Security Notes

- Change default user credentials before deployment
- Update Flask secret key for production
- Use HTTPS in production environments
- Implement rate limiting for login attempts
- Add CSRF protection for forms

## Future Enhancements

- [ ] React frontend migration
- [ ] WebSocket for real-time updates
- [ ] Multi-user support with database
- [ ] Email notifications
- [ ] Mobile app version
- [ ] Advanced analytics with ML insights
- [ ] Study recommendations based on focus patterns

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: support@focuscheck.com (if applicable)

## Acknowledgments

- PyTorch team for the deep learning framework
- ResNet18 architecture by Microsoft Research
- Flask community for the web framework
- Chart.js for beautiful visualizations

---

**Made with ❤️ for students who want to improve their focus and productivity**

*Version: 1.0.0*
*Last Updated: 2025*
