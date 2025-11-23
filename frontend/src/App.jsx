import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';
import RootRedirect from './components/RootRedirect';
import AuthErrorToast from './components/AuthErrorToast';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import AdminDashboard from './pages/AdminDashboard';
import FocusSession from './pages/FocusSession';
import PendingApproval from './pages/PendingApproval';

import './index.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        {/* Global auth error toast */}
        <AuthErrorToast />
        <Routes>
          {/* Public Routes - redirect to dashboard if already logged in */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
          />

          {/* Pending Approval - for teachers awaiting admin approval */}
          <Route
            path="/pending-approval"
            element={
              <ProtectedRoute allowedRoles={['teacher']}>
                <PendingApproval />
              </ProtectedRoute>
            }
          />

          {/* Student Routes */}
          <Route
            path="/student"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <StudentDashboard />
              </ProtectedRoute>
            }
          />

          {/* Teacher Routes */}
          <Route
            path="/teacher"
            element={
              <ProtectedRoute allowedRoles={['teacher']}>
                <TeacherDashboard />
              </ProtectedRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          {/* Focus Session Route - All authenticated users */}
          <Route
            path="/session/:sessionId"
            element={
              <ProtectedRoute allowedRoles={['student', 'teacher', 'admin']}>
                <FocusSession />
              </ProtectedRoute>
            }
          />

          {/* Root - smart redirect based on auth status */}
          <Route path="/" element={<RootRedirect />} />

          {/* Catch all - smart redirect */}
          <Route path="*" element={<RootRedirect />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
