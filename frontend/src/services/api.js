import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const API = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Store for auth-related callbacks
let authCallbacks = {
  onUnauthorized: null,
  onForbidden: null,
};

// Setup function to be called from AuthProvider
export const setupInterceptors = (callbacks) => {
  authCallbacks = { ...authCallbacks, ...callbacks };
};

// Response interceptor for handling auth errors
API.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url;

    // Skip auth check endpoint to avoid loops
    if (requestUrl === '/auth/me') {
      return Promise.reject(error);
    }

    if (status === 401) {
      // Session expired or not authenticated
      if (authCallbacks.onUnauthorized) {
        authCallbacks.onUnauthorized();
      }
    } else if (status === 403) {
      // User doesn't have permission
      if (authCallbacks.onForbidden) {
        authCallbacks.onForbidden(error.response?.data?.error || 'You do not have permission to perform this action.');
      }
    }

    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  login: (email, password) => API.post('/auth/login', { email, password }),
  register: (name, email, password, role) => API.post('/auth/register', { name, email, password, role }),
  logout: () => API.post('/auth/logout'),
  getMe: () => API.get('/auth/me'),
};

// Student endpoints
export const studentAPI = {
  getEnrolledCourses: () => API.get('/student/courses/enrolled'),
  getAvailableCourses: () => API.get('/student/courses/available'),
  enrollCourse: (courseId) => API.post(`/student/courses/${courseId}/enroll`),
  unenrollCourse: (courseId) => API.post(`/student/courses/${courseId}/unenroll`),
  getEnrollmentRequests: () => API.get('/student/enrollment-requests'),
  getReports: () => API.get('/student/reports'),
  downloadReport: (reportId) => `${API_BASE_URL}/student/reports/${reportId}/download`,
};

// Teacher endpoints
export const teacherAPI = {
  getCourses: () => API.get('/teacher/courses'),
  getCourseStudents: (courseId) => API.get(`/teacher/courses/${courseId}/students`),
  getSessions: () => API.get('/teacher/sessions'),
  createSession: (data) => API.post('/teacher/sessions', data),
  endSession: (sessionId) => API.post(`/teacher/sessions/${sessionId}/end`),
  getEnrollmentRequests: () => API.get('/teacher/enrollment-requests'),
  approveEnrollment: (requestId) => API.post(`/teacher/enrollment-requests/${requestId}/approve`),
  rejectEnrollment: (requestId) => API.post(`/teacher/enrollment-requests/${requestId}/reject`),
  getReports: () => API.get('/teacher/reports'),
  downloadStudentReportUrl: (reportId) => `${API_BASE_URL}/teacher/reports/${reportId}/download`,
  downloadCombinedReportUrl: (sessionId) => `${API_BASE_URL}/teacher/sessions/${sessionId}/download`,
};

// Admin endpoints
export const adminAPI = {
  getUsers: () => API.get('/admin/users'),
  getPendingTeachers: () => API.get('/admin/teachers/pending'),
  getApprovedTeachers: () => API.get('/admin/teachers/approved'),
  approveTeacher: (teacherId) => API.post(`/admin/teachers/approve/${teacherId}`),
  rejectTeacher: (teacherId) => API.post(`/admin/teachers/reject/${teacherId}`),
  deleteTeacher: (teacherId) => API.delete(`/admin/teachers/${teacherId}`),
  deleteStudent: (studentId) => API.delete(`/admin/students/${studentId}`),
  getCourses: () => API.get('/admin/courses'),
  createCourse: (data) => API.post('/admin/courses/add', data),
  updateCourse: (courseId, data) => API.put(`/admin/courses/${courseId}`, data),
  getStats: () => API.get('/admin/statistics'),
};

// Session (Focus Detection) endpoints
export const sessionAPI = {
  start: (sessionId) => API.post(`/session/${sessionId}/start`),
  stop: (sessionId) => API.post(`/session/${sessionId}/stop`),
  recordTabSwitch: (sessionId, data) => API.post(`/session/${sessionId}/tab-switch`, data),
  getVideoFeedUrl: (sessionId) => `${API_BASE_URL}/session/${sessionId}/video_feed`,
};

export default API;
