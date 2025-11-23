import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { teacherAPI } from '../services/api';
import Navbar from '../components/Navbar';
import Toast from '../components/Toast';
import WelcomeCard from '../components/WelcomeCard';
import ConfirmDialog from '../components/ConfirmDialog';
import { formatDateTimeWithRelative, formatDuration } from '../utils/dateFormat';
import '../styles/Dashboard.css';

const STORAGE_KEY = 'teacher_dashboard_tab';

const TeacherDashboard = () => {
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) || 'courses';
  });
  const [courses, setCourses] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [enrollmentRequests, setEnrollmentRequests] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  // Action loading states
  const [endingSessionId, setEndingSessionId] = useState(null);
  const [approvingId, setApprovingId] = useState(null);
  const [rejectingId, setRejectingId] = useState(null);
  const [creatingSession, setCreatingSession] = useState(false);

  // Create session form
  const [sessionName, setSessionName] = useState('');
  const [selectedCourse, setSelectedCourse] = useState('');
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');

  // Confirm dialog
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false });

  // Students modal
  const [showStudentsModal, setShowStudentsModal] = useState(false);
  const [modalStudents, setModalStudents] = useState([]);
  const [modalCourse, setModalCourse] = useState(null);

  // Highlight newly created session
  const [highlightedSessionId, setHighlightedSessionId] = useState(null);

  // Report filters
  const [reportCourseFilter, setReportCourseFilter] = useState('all');
  const [reportSort, setReportSort] = useState('newest');

  const { user } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    localStorage.setItem(STORAGE_KEY, tab);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadCourses(),
        loadSessions(),
        loadEnrollmentRequests(),
        loadReports(),
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadCourses = async () => {
    try {
      const response = await teacherAPI.getCourses();
      setCourses(response.data.courses || []);
    } catch (error) {
      console.error('Error loading courses:', error);
    }
  };

  const loadSessions = async () => {
    try {
      const response = await teacherAPI.getSessions();
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const loadEnrollmentRequests = async () => {
    try {
      const response = await teacherAPI.getEnrollmentRequests();
      setEnrollmentRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error loading enrollment requests:', error);
    }
  };

  const loadReports = async () => {
    try {
      const response = await teacherAPI.getReports();
      setReports(response.data.reports || []);
    } catch (error) {
      console.error('Error loading reports:', error);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');

    if (!selectedCourse) {
      setFormError('Please select a course');
      return;
    }

    setCreatingSession(true);
    try {
      const response = await teacherAPI.createSession({
        course_id: selectedCourse,
        session_name: sessionName,
      });
      const newSessionId = response.data?.session?.id || response.data?.session_id;

      setFormSuccess('Session created successfully! Switching to Sessions tab...');
      setSessionName('');
      setSelectedCourse('');
      await loadSessions();

      // Set highlight and switch to sessions tab
      if (newSessionId) {
        setHighlightedSessionId(newSessionId);
        // Clear highlight after 3 seconds
        setTimeout(() => setHighlightedSessionId(null), 3000);
      }

      setTimeout(() => handleTabChange('sessions'), 800);
    } catch (error) {
      setFormError(error.response?.data?.error || 'Failed to create session');
    } finally {
      setCreatingSession(false);
    }
  };

  const handleEndSession = (sessionId, sessionName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'End Session',
      message: `Are you sure you want to end "${sessionName}"?`,
      description: 'All students currently in this session will be disconnected and their focus data will be saved.',
      type: 'warning',
      onConfirm: async () => {
        setEndingSessionId(sessionId);
        try {
          await teacherAPI.endSession(sessionId);
          showToast('Session ended successfully', 'success');
          loadSessions();
        } catch (error) {
          showToast(error.response?.data?.error || 'Failed to end session', 'error');
        } finally {
          setEndingSessionId(null);
          setConfirmDialog({ isOpen: false });
        }
      },
    });
  };

  const handleApproveEnrollment = async (requestId) => {
    setApprovingId(requestId);
    try {
      await teacherAPI.approveEnrollment(requestId);
      showToast('Enrollment approved!', 'success');
      loadEnrollmentRequests();
      loadCourses();
    } catch (error) {
      showToast(error.response?.data?.error || 'Failed to approve', 'error');
    } finally {
      setApprovingId(null);
    }
  };

  const handleRejectEnrollment = (requestId, studentName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Reject Enrollment',
      message: `Reject ${studentName}'s enrollment request?`,
      description: 'The student will be notified that their request was rejected.',
      type: 'danger',
      onConfirm: async () => {
        setRejectingId(requestId);
        try {
          await teacherAPI.rejectEnrollment(requestId);
          showToast('Enrollment rejected', 'info');
          loadEnrollmentRequests();
        } catch (error) {
          showToast(error.response?.data?.error || 'Failed to reject', 'error');
        } finally {
          setRejectingId(null);
          setConfirmDialog({ isOpen: false });
        }
      },
    });
  };

  const viewStudents = async (courseId) => {
    try {
      const response = await teacherAPI.getCourseStudents(courseId);
      setModalStudents(response.data.students || []);
      setModalCourse(response.data.course);
      setShowStudentsModal(true);
    } catch (error) {
      showToast('Failed to load students', 'error');
    }
  };

  const downloadReport = async (reportId) => {
    try {
      const response = await fetch(`http://localhost:5000/teacher/reports/${reportId}/download`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to download report');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `focus_report_${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      showToast('Failed to download report', 'error');
    }
  };

  const downloadCombinedReport = async (sessionId) => {
    try {
      const response = await fetch(`http://localhost:5000/teacher/sessions/${sessionId}/download`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to download combined report');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session_report_${sessionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      showToast('Failed to download combined report', 'error');
    }
  };

  const copySessionLink = async (sessionId) => {
    const sessionUrl = `${window.location.origin}/session/${sessionId}`;
    try {
      await navigator.clipboard.writeText(sessionUrl);
      showToast('Session link copied to clipboard!', 'success');
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = sessionUrl;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      showToast('Session link copied to clipboard!', 'success');
    }
  };

  const showToast = (message, type) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Calculate stats for welcome card
  const getWelcomeStats = () => {
    const activeSessions = sessions.filter(s => s.status === 'active').length;
    const totalStudents = courses.reduce((acc, c) => acc + (c.student_count || 0), 0);
    return [
      { value: courses.length, label: 'Courses' },
      { value: activeSessions, label: 'Active Sessions' },
      { value: totalStudents, label: 'Students' },
    ];
  };

  // Derived data for shortcuts
  const pendingRequestsCount = enrollmentRequests.length;
  const activeSessionsCount = sessions.filter(s => s.status === 'active').length;

  const getFocusClass = (percentage) => {
    if (percentage >= 70) return 'good';
    if (percentage >= 50) return 'medium';
    return 'low';
  };

  // Filter and sort reports
  const getFilteredReports = () => {
    let filtered = [...reports];

    // Filter by course
    if (reportCourseFilter !== 'all') {
      filtered = filtered.filter(r => r.course?.id === reportCourseFilter);
    }

    // Sort
    if (reportSort === 'newest') {
      filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (reportSort === 'oldest') {
      filtered.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (reportSort === 'highest') {
      filtered.sort((a, b) => b.focus_percentage - a.focus_percentage);
    } else if (reportSort === 'lowest') {
      filtered.sort((a, b) => a.focus_percentage - b.focus_percentage);
    }

    return filtered;
  };

  return (
    <div className="dashboard">
      <Navbar />
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        description={confirmDialog.description}
        type={confirmDialog.type}
        confirmText="Yes, Confirm"
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false })}
        loading={endingSessionId !== null || rejectingId !== null}
      />

      <div className="container">
        {/* Welcome Card */}
        <WelcomeCard user={user} stats={getWelcomeStats()} />

        {/* Shortcut Cards */}
        {!loading && (pendingRequestsCount > 0 || activeSessionsCount > 0) && (
          <div className="shortcuts-grid">
            {pendingRequestsCount > 0 && (
              <div
                className="shortcut-card warning"
                onClick={() => handleTabChange('enrollments')}
              >
                <div className="shortcut-icon">
                  <i className="ri-user-add-line"></i>
                </div>
                <div className="shortcut-info">
                  <div className="shortcut-value">{pendingRequestsCount}</div>
                  <div className="shortcut-label">Pending Requests</div>
                </div>
                <i className="ri-arrow-right-line shortcut-arrow"></i>
              </div>
            )}
            {activeSessionsCount > 0 && (
              <div
                className="shortcut-card success"
                onClick={() => handleTabChange('sessions')}
              >
                <div className="shortcut-icon">
                  <i className="ri-broadcast-line"></i>
                </div>
                <div className="shortcut-info">
                  <div className="shortcut-value">{activeSessionsCount}</div>
                  <div className="shortcut-label">Active Sessions</div>
                </div>
                <i className="ri-arrow-right-line shortcut-arrow"></i>
              </div>
            )}
          </div>
        )}

        <div className="section">
          <div className="tabs">
            <button className={`tab ${activeTab === 'courses' ? 'active' : ''}`} onClick={() => handleTabChange('courses')}>
              My Courses
            </button>
            <button className={`tab ${activeTab === 'sessions' ? 'active' : ''}`} onClick={() => handleTabChange('sessions')}>
              Sessions
            </button>
            <button className={`tab ${activeTab === 'enrollments' ? 'active' : ''}`} onClick={() => handleTabChange('enrollments')}>
              Enrollment Requests {pendingRequestsCount > 0 && <span className="tab-badge">{pendingRequestsCount}</span>}
            </button>
            <button className={`tab ${activeTab === 'create' ? 'active' : ''}`} onClick={() => handleTabChange('create')}>
              Create Session
            </button>
            <button className={`tab ${activeTab === 'reports' ? 'active' : ''}`} onClick={() => handleTabChange('reports')}>
              Reports
            </button>
          </div>

          {/* Courses Tab */}
          {activeTab === 'courses' && (
            <div className="tab-content active">
              <h2><i className="ri-book-line"></i> My Courses</h2>
              {loading ? (
                <div className="loading">Loading courses...</div>
              ) : courses.length > 0 ? (
                <div className="courses-grid">
                  {courses.map((course) => (
                    <div key={course.id} className="course-card teacher">
                      <div className="course-code">{course.course_code}</div>
                      <div className="course-name">{course.course_name}</div>
                      <div className="course-info">
                        <span><i className="ri-group-line"></i> {course.student_count} students</span>
                      </div>
                      <button className="btn btn-primary" onClick={() => viewStudents(course.id)}>
                        <i className="ri-user-line"></i> View Students
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-book-open-line"></i>
                  <p>No courses assigned yet. Contact admin to assign courses.</p>
                </div>
              )}
            </div>
          )}

          {/* Sessions Tab */}
          {activeTab === 'sessions' && (
            <div className="tab-content active">
              <h2><i className="ri-calendar-line"></i> My Sessions</h2>
              {loading ? (
                <div className="loading">Loading sessions...</div>
              ) : sessions.length > 0 ? (
                <div className="sessions-list">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className={`session-item ${highlightedSessionId === session.id ? 'highlighted' : ''}`}
                    >
                      <div className="session-info">
                        <div className="session-name">{session.session_name}</div>
                        <div className="course-code">
                          {session.course?.course_code} - {session.course?.course_name}
                        </div>
                        <div className="session-details">
                          <span><i className="ri-calendar-line"></i> {formatDateTimeWithRelative(session.start_time)}</span>
                          {session.status !== 'active' && session.end_time && (
                            <span><i className="ri-check-line"></i> Ended: {formatDateTimeWithRelative(session.end_time)}</span>
                          )}
                        </div>
                      </div>
                      <div className="session-actions">
                        <span className={`session-status status-${session.status}`}>
                          {session.status.toUpperCase()}
                        </span>
                        {session.status === 'active' ? (
                          <>
                            <button
                              className="btn btn-secondary"
                              onClick={() => copySessionLink(session.id)}
                              title="Copy session link to share with students"
                            >
                              <i className="ri-link"></i> Copy Link
                            </button>
                            <button
                              className="btn btn-danger"
                              onClick={() => handleEndSession(session.id, session.session_name)}
                              disabled={endingSessionId === session.id}
                            >
                              {endingSessionId === session.id ? (
                                <><i className="ri-loader-4-line ri-spin"></i> Ending...</>
                              ) : (
                                <><i className="ri-stop-line"></i> End Session</>
                              )}
                            </button>
                          </>
                        ) : (
                          <button className="btn btn-success" onClick={() => downloadCombinedReport(session.id)}>
                            <i className="ri-download-2-line"></i> Download Report
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-calendar-line"></i>
                  <p>No sessions created yet. Create your first session!</p>
                </div>
              )}
            </div>
          )}

          {/* Enrollment Requests Tab */}
          {activeTab === 'enrollments' && (
            <div className="tab-content active">
              <h2><i className="ri-user-add-line"></i> Pending Enrollment Requests</h2>
              {loading ? (
                <div className="loading">Loading requests...</div>
              ) : enrollmentRequests.length > 0 ? (
                <div className="enrollment-list">
                  {enrollmentRequests.map((request) => (
                    <div key={request.id} className="enrollment-card">
                      <div className="enrollment-info">
                        <div className="enrollment-student">
                          <i className="ri-user-line"></i> {request.student.name}
                        </div>
                        <div className="enrollment-course">
                          <i className="ri-book-line"></i> {request.course.course_code} - {request.course.course_name}
                        </div>
                        <div className="enrollment-date">
                          <i className="ri-calendar-line"></i> {formatDateTimeWithRelative(request.created_at)}
                        </div>
                      </div>
                      <div className="enrollment-actions">
                        <button
                          className="btn btn-success"
                          onClick={() => handleApproveEnrollment(request.id)}
                          disabled={approvingId === request.id}
                        >
                          {approvingId === request.id ? (
                            <><i className="ri-loader-4-line ri-spin"></i> Approving...</>
                          ) : (
                            <><i className="ri-check-line"></i> Approve</>
                          )}
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleRejectEnrollment(request.id, request.student.name)}
                          disabled={rejectingId === request.id}
                        >
                          {rejectingId === request.id ? (
                            <><i className="ri-loader-4-line ri-spin"></i> Rejecting...</>
                          ) : (
                            <><i className="ri-close-line"></i> Reject</>
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-user-add-line"></i>
                  <p>No pending enrollment requests</p>
                </div>
              )}
            </div>
          )}

          {/* Create Session Tab */}
          {activeTab === 'create' && (
            <div className="tab-content active">
              <h2><i className="ri-add-circle-line"></i> Create New Session</h2>

              {formError && <div className="error-message show">{formError}</div>}
              {formSuccess && <div className="success-message show">{formSuccess}</div>}

              <div className="create-session-form">
                <form onSubmit={handleCreateSession}>
                  <div className="form-group">
                    <label htmlFor="courseSelect">Select Course</label>
                    <select
                      id="courseSelect"
                      value={selectedCourse}
                      onChange={(e) => setSelectedCourse(e.target.value)}
                      required
                    >
                      <option value="">Select a course</option>
                      {courses.map((course) => (
                        <option key={course.id} value={course.id}>
                          {course.course_code} - {course.course_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="sessionName">Session Name</label>
                    <input
                      type="text"
                      id="sessionName"
                      value={sessionName}
                      onChange={(e) => setSessionName(e.target.value)}
                      required
                      placeholder="e.g., Week 5 Lecture - Introduction"
                    />
                  </div>

                  <button type="submit" className="btn btn-success full-width" disabled={creatingSession}>
                    {creatingSession ? (
                      <><i className="ri-loader-4-line ri-spin"></i> Creating...</>
                    ) : (
                      <><i className="ri-add-line"></i> Create Session</>
                    )}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <div className="tab-content active">
              <div className="reports-header">
                <h2><i className="ri-file-chart-line"></i> Student Focus Reports</h2>
                {reports.length > 0 && (
                  <div className="reports-filters">
                    <select
                      value={reportCourseFilter}
                      onChange={(e) => setReportCourseFilter(e.target.value)}
                      className="filter-select"
                    >
                      <option value="all">All Courses</option>
                      {courses.map(course => (
                        <option key={course.id} value={course.id}>
                          {course.course_code}
                        </option>
                      ))}
                    </select>
                    <select
                      value={reportSort}
                      onChange={(e) => setReportSort(e.target.value)}
                      className="filter-select"
                    >
                      <option value="newest">Newest First</option>
                      <option value="oldest">Oldest First</option>
                      <option value="highest">Highest Focus</option>
                      <option value="lowest">Lowest Focus</option>
                    </select>
                  </div>
                )}
              </div>
              {loading ? (
                <div className="loading">Loading reports...</div>
              ) : reports.length > 0 ? (
                <div className="reports-list">
                  {getFilteredReports().map((report) => (
                    <div key={report.id} className="report-item">
                      <div className="report-info">
                        <div className="report-course">
                          <strong>{report.student?.name}</strong> - {report.course?.course_code}
                        </div>
                        <div className="report-date">
                          {report.session?.session_name} | {formatDateTimeWithRelative(report.created_at)} ({formatDuration(report.duration)})
                        </div>
                      </div>
                      <div className={`focus-score ${getFocusClass(report.focus_percentage)}`}>
                        {report.focus_percentage}%
                      </div>
                      <button className="btn btn-primary" onClick={() => downloadReport(report.id)}>
                        <i className="ri-download-line"></i> PDF
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-file-list-line"></i>
                  <p>No reports yet. Students will generate reports after joining focus detection sessions.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Students Modal */}
      {showStudentsModal && (
        <div className="modal show" onClick={(e) => e.target.className.includes('modal') && setShowStudentsModal(false)}>
          <div className="modal-content">
            <div className="modal-header">
              <h3>Enrolled Students - {modalCourse?.course_name}</h3>
              <button className="close-modal" onClick={() => setShowStudentsModal(false)}>
                <i className="ri-close-line"></i>
              </button>
            </div>
            <div className="modal-body">
              {modalStudents.length > 0 ? (
                <table className="students-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Student Name</th>
                      <th>Email</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modalStudents.map((student, index) => (
                      <tr key={student.id}>
                        <td>{index + 1}</td>
                        <td>{student.name}</td>
                        <td>{student.email}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">No students enrolled yet</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherDashboard;
