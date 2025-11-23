import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { studentAPI } from '../services/api';
import Navbar from '../components/Navbar';
import Toast from '../components/Toast';
import WelcomeCard from '../components/WelcomeCard';
import NextStepBanner from '../components/NextStepBanner';
import ActiveSessionBanner from '../components/ActiveSessionBanner';
import ConfirmDialog from '../components/ConfirmDialog';
import ReportBadge from '../components/ReportBadge';
import { formatDateTimeWithRelative, formatDuration } from '../utils/dateFormat';
import '../styles/Dashboard.css';

const STORAGE_KEY = 'student_dashboard_tab';

const StudentDashboard = () => {
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) || 'courses';
  });
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [enrollmentRequests, setEnrollmentRequests] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  // Action loading states
  const [enrollingId, setEnrollingId] = useState(null);
  const [unenrollingId, setUnenrollingId] = useState(null);

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false });

  // Report filters
  const [reportFilter, setReportFilter] = useState('all');
  const [reportSort, setReportSort] = useState('newest');

  // Track newly requested courses and highlighted enrollment
  const [requestedCourseIds, setRequestedCourseIds] = useState(new Set());
  const [highlightedRequestId, setHighlightedRequestId] = useState(null);

  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  // Save tab to localStorage
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    localStorage.setItem(STORAGE_KEY, tab);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadEnrolledCourses(),
        loadAvailableCourses(),
        loadEnrollmentRequests(),
        loadReports(),
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadEnrolledCourses = async () => {
    try {
      const response = await studentAPI.getEnrolledCourses();
      setEnrolledCourses(response.data.courses || []);
    } catch (error) {
      console.error('Error loading enrolled courses:', error);
    }
  };

  const loadAvailableCourses = async () => {
    try {
      const response = await studentAPI.getAvailableCourses();
      setAvailableCourses(response.data.courses || []);
    } catch (error) {
      console.error('Error loading available courses:', error);
    }
  };

  const loadEnrollmentRequests = async () => {
    try {
      const response = await studentAPI.getEnrollmentRequests();
      setEnrollmentRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error loading enrollment requests:', error);
    }
  };

  const loadReports = async () => {
    try {
      const response = await studentAPI.getReports();
      setReports(response.data.reports || []);
    } catch (error) {
      console.error('Error loading reports:', error);
    }
  };

  const handleEnroll = async (courseId) => {
    setEnrollingId(courseId);
    try {
      const response = await studentAPI.enrollCourse(courseId);
      showToast('Enrollment request sent!', 'success');

      // Mark this course as requested (for immediate UI feedback)
      setRequestedCourseIds(prev => new Set([...prev, courseId]));

      // Reload data and get new request ID
      await loadEnrollmentRequests();

      // Find the new request and highlight it
      const newRequestId = response.data?.request_id || response.data?.enrollment_request?.id;
      if (newRequestId) {
        setHighlightedRequestId(newRequestId);
        setTimeout(() => setHighlightedRequestId(null), 3000);
      }

      // Auto-switch to Enrollment Requests tab
      setTimeout(() => handleTabChange('requests'), 500);
    } catch (error) {
      showToast(error.response?.data?.error || 'Failed to enroll', 'error');
    } finally {
      setEnrollingId(null);
    }
  };

  const handleUnenroll = (courseId, courseName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Unenroll from Course',
      message: `Are you sure you want to unenroll from ${courseName}?`,
      description: "You will lose access to this course's sessions and won't be able to join future focus detection sessions.",
      type: 'danger',
      onConfirm: async () => {
        setUnenrollingId(courseId);
        try {
          await studentAPI.unenrollCourse(courseId);
          showToast('Unenrolled successfully!', 'success');
          loadEnrolledCourses();
          loadAvailableCourses();
        } catch (error) {
          showToast(error.response?.data?.error || 'Failed to unenroll', 'error');
        } finally {
          setUnenrollingId(null);
          setConfirmDialog({ isOpen: false });
        }
      },
    });
  };

  const joinSession = (sessionId) => {
    navigate(`/session/${sessionId}`);
  };

  const downloadReport = (reportId) => {
    window.location.href = studentAPI.downloadReport(reportId);
  };

  const showToast = (message, type) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Calculate stats for welcome card
  const getWelcomeStats = () => {
    const lastReport = reports[0];
    return [
      { value: enrolledCourses.length, label: 'Courses' },
      { value: reports.length, label: 'Reports' },
      { value: lastReport ? `${lastReport.focus_percentage}%` : 'N/A', label: 'Last Focus' },
    ];
  };

  // Determine which banner to show
  const getNextStepBanner = () => {
    if (enrolledCourses.length === 0) {
      return { type: 'no_courses', onAction: () => handleTabChange('available') };
    }

    // Check for active session - will be handled separately with ActiveSessionBanner
    const activeSession = enrolledCourses.find(c => c.has_active_session);
    if (activeSession) {
      return null; // Active session uses different banner
    }

    return { type: 'no_active_session' };
  };

  // Get active session data for the new banner
  const getActiveSession = () => {
    return enrolledCourses.find(c => c.has_active_session);
  };

  // Filter and sort reports
  const getFilteredReports = () => {
    let filtered = [...reports];

    // Filter by course
    if (reportFilter !== 'all') {
      filtered = filtered.filter(r => r.course?.id === reportFilter);
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

  // Get unique courses for filter
  const getUniqueCourses = () => {
    const courseMap = new Map();
    reports.forEach(r => {
      if (r.course) {
        courseMap.set(r.course.id, r.course);
      }
    });
    return Array.from(courseMap.values());
  };

  const nextStep = getNextStepBanner();
  const activeSession = getActiveSession();

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
        confirmText="Yes, Unenroll"
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false })}
        loading={unenrollingId !== null}
      />

      <div className="container">
        {/* Welcome Card */}
        <WelcomeCard user={user} stats={getWelcomeStats()} />

        {/* Active Session Banner - special design for live sessions */}
        {!loading && activeSession && (
          <ActiveSessionBanner
            courseName={activeSession.course_name}
            courseCode={activeSession.course_code}
            sessionName={activeSession.active_session_name}
            sessionId={activeSession.active_session_id}
            teacherName={activeSession.teacher?.name}
          />
        )}

        {/* Smart Next Step Banner (for non-active-session states) */}
        {!loading && nextStep && <NextStepBanner {...nextStep} />}

        <div className="section">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'courses' ? 'active' : ''}`}
              onClick={() => handleTabChange('courses')}
            >
              My Courses
            </button>
            <button
              className={`tab ${activeTab === 'available' ? 'active' : ''}`}
              onClick={() => handleTabChange('available')}
            >
              Available Courses
            </button>
            <button
              className={`tab ${activeTab === 'requests' ? 'active' : ''}`}
              onClick={() => handleTabChange('requests')}
            >
              Enrollment Requests
              {enrollmentRequests.filter(r => r.status === 'pending').length > 0 && (
                <span className="tab-badge">{enrollmentRequests.filter(r => r.status === 'pending').length}</span>
              )}
            </button>
            <button
              className={`tab ${activeTab === 'reports' ? 'active' : ''}`}
              onClick={() => handleTabChange('reports')}
            >
              My Reports
            </button>
          </div>

          {/* Enrolled Courses Tab */}
          {activeTab === 'courses' && (
            <div className="tab-content active">
              <h2><i className="ri-book-line"></i> My Enrolled Courses</h2>
              {loading ? (
                <div className="loading">Loading courses...</div>
              ) : enrolledCourses.length > 0 ? (
                <div className="courses-grid">
                  {enrolledCourses.map((course) => (
                    <div key={course.id} className="course-card enrolled">
                      <div className="course-code">{course.course_code}</div>
                      <div className="course-name">{course.course_name}</div>
                      <div className="course-info">
                        <span><i className="ri-user-line"></i> {course.teacher?.name}</span>
                        {course.has_active_session && (
                          <span className="active-session-badge">Active Session</span>
                        )}
                      </div>
                      {course.has_active_session ? (
                        <button
                          className="btn btn-success"
                          onClick={() => joinSession(course.active_session_id)}
                        >
                          <i className="ri-play-line"></i> Join Session
                        </button>
                      ) : (
                        <div className="no-session">No active session</div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-book-open-line"></i>
                  <p>You haven't enrolled in any courses yet</p>
                </div>
              )}
            </div>
          )}

          {/* Available Courses Tab */}
          {activeTab === 'available' && (
            <div className="tab-content active">
              <h2><i className="ri-add-circle-line"></i> Browse Available Courses</h2>
              {loading ? (
                <div className="loading">Loading courses...</div>
              ) : availableCourses.length > 0 ? (
                <div className="courses-grid">
                  {availableCourses.map((course) => (
                    <div key={course.id} className={`course-card ${course.is_enrolled ? 'enrolled' : ''}`}>
                      <div className="course-code">{course.course_code}</div>
                      <div className="course-name">{course.course_name}</div>
                      <div className="course-info">
                        <span><i className="ri-user-line"></i> {course.teacher?.name || 'N/A'}</span>
                        <span><i className="ri-group-line"></i> {course.student_count} students</span>
                      </div>
                      {!course.is_enrolled ? (
                        requestedCourseIds.has(course.id) || course.has_pending_request ? (
                          <button className="btn btn-secondary" disabled>
                            <i className="ri-time-line"></i> Requested
                          </button>
                        ) : (
                          <button
                            className="btn btn-primary"
                            onClick={() => handleEnroll(course.id)}
                            disabled={enrollingId === course.id}
                          >
                            {enrollingId === course.id ? (
                              <><i className="ri-loader-4-line ri-spin"></i> Enrolling...</>
                            ) : (
                              <><i className="ri-add-line"></i> Enroll</>
                            )}
                          </button>
                        )
                      ) : (
                        <button
                          className="btn btn-danger"
                          onClick={() => handleUnenroll(course.id, course.course_name)}
                          disabled={unenrollingId === course.id}
                        >
                          {unenrollingId === course.id ? (
                            <><i className="ri-loader-4-line ri-spin"></i> Unenrolling...</>
                          ) : (
                            <><i className="ri-close-line"></i> Unenroll</>
                          )}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-search-line"></i>
                  <p>No courses available</p>
                </div>
              )}
            </div>
          )}

          {/* Enrollment Requests Tab */}
          {activeTab === 'requests' && (
            <div className="tab-content active">
              <h2><i className="ri-time-line"></i> My Enrollment Requests</h2>
              {loading ? (
                <div className="loading">Loading requests...</div>
              ) : enrollmentRequests.length > 0 ? (
                <div className="request-list">
                  {enrollmentRequests.map((request) => (
                    <div
                      key={request.id}
                      className={`request-card ${highlightedRequestId === request.id ? 'highlighted' : ''}`}
                    >
                      <div className="request-info">
                        <div className="request-course">
                          <i className="ri-book-line"></i> {request.course.course_code} - {request.course.course_name}
                        </div>
                        <div className="request-date">
                          <i className="ri-calendar-line"></i> {formatDateTimeWithRelative(request.created_at)}
                        </div>
                        <div className={`enrollment-status status-${request.status}`}>
                          {request.status === 'pending' && 'Pending Approval'}
                          {request.status === 'approved' && 'Approved'}
                          {request.status === 'rejected' && 'Rejected'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-file-list-line"></i>
                  <p>No enrollment requests yet. Browse available courses to request enrollment!</p>
                </div>
              )}
            </div>
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <div className="tab-content active">
              <div className="reports-header">
                <h2><i className="ri-file-chart-line"></i> Focus Reports</h2>
                {reports.length > 0 && (
                  <div className="reports-filters">
                    <select
                      value={reportFilter}
                      onChange={(e) => setReportFilter(e.target.value)}
                      className="filter-select"
                    >
                      <option value="all">All Courses</option>
                      {getUniqueCourses().map(course => (
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
                          {report.course?.course_code} - {report.course?.course_name}
                        </div>
                        <div className="report-date">
                          {formatDateTimeWithRelative(report.created_at)} - {report.session?.session_name} ({formatDuration(report.duration)})
                        </div>
                      </div>
                      <ReportBadge percentage={report.focus_percentage} />
                      <div className="focus-score-container">
                        <span className={`focus-score ${report.focus_percentage >= 70 ? 'good' : report.focus_percentage >= 50 ? 'medium' : 'low'}`}>
                          {report.focus_percentage}%
                        </span>
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
                  <p>No reports yet. Join a session to generate your first report!</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
