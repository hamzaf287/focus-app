import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';
import Navbar from '../components/Navbar';
import Toast from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';
import '../styles/Dashboard.css';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [courses, setCourses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [pendingTeachers, setPendingTeachers] = useState([]);

  // Create Course form state
  const [approvedTeachers, setApprovedTeachers] = useState([]);
  const [courseCode, setCourseCode] = useState('');
  const [courseName, setCourseName] = useState('');
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [creatingCourse, setCreatingCourse] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  // Edit Course modal state
  const [editingCourse, setEditingCourse] = useState(null);
  const [editCourseName, setEditCourseName] = useState('');
  const [editTeacherId, setEditTeacherId] = useState('');
  const [savingCourse, setSavingCourse] = useState(false);
  const [editFormErrors, setEditFormErrors] = useState({});

  // User details modal state
  const [viewingUser, setViewingUser] = useState(null);

  // Role filter state for All Users tab
  const [roleFilter, setRoleFilter] = useState('all'); // 'all', 'teacher', 'student'

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false });

  const { user } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([loadUsers(), loadCourses(), loadStats(), loadApprovedTeachers()]);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const [usersRes, pendingRes] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getPendingTeachers(),
      ]);

      const pendingMap = new Map(
        (pendingRes.data?.teachers || []).map((t) => [t.id, t])
      );

      const teachers = (usersRes.data?.teachers || []).map((t) => ({
        ...t,
        role: 'teacher',
        status: t.status || (t.approved ? 'approved' : 'pending'),
        created_at: t.created_at || pendingMap.get(t.id)?.created_at,
      }));

      const students = (usersRes.data?.students || []).map((s) => ({
        ...s,
        role: 'student',
        status: 'approved',
      }));

      setUsers([...teachers, ...students]);
      setPendingTeachers(teachers.filter((t) => t.status === 'pending'));
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadCourses = async () => {
    try {
      const response = await adminAPI.getCourses();
      const rawCourses = response.data.courses || [];
      // Normalize shape so course.teacher is available (id + name)
      const normalized = rawCourses.map((course) => ({
        ...course,
        teacher: course.teacher || (course.teacher_id
          ? { id: course.teacher_id, name: course.teacher_name }
          : null),
      }));
      setCourses(normalized);
    } catch (error) {
      console.error('Error loading courses:', error);
    }
  };

  const loadApprovedTeachers = async () => {
    try {
      const response = await adminAPI.getApprovedTeachers();
      setApprovedTeachers(response.data.teachers || []);
    } catch (error) {
      console.error('Error loading approved teachers:', error);
      // Don't fallback to users state here - it may not be populated yet
      // The API endpoint should be the source of truth
      setApprovedTeachers([]);
    }
  };

  const loadStats = async () => {
    try {
      const response = await adminAPI.getStats();
      const data = response.data || {};
      setStats({
        total_users: (data.total_students || 0) + (data.total_teachers || 0),
        total_teachers: data.total_teachers || 0,
        total_students: data.total_students || 0,
        total_courses: data.total_courses || 0,
        pending_teachers: data.pending_teachers || 0,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleApproveTeacher = async (userId) => {
    try {
      await adminAPI.approveTeacher(userId);
      showToast('Teacher approved successfully', 'success');
      loadUsers();
      loadApprovedTeachers();
      loadStats();
    } catch (error) {
      showToast(error.response?.data?.error || 'Failed to approve teacher', 'error');
    }
  };

  const handleRejectTeacher = (userId, teacherName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Reject Teacher',
      message: `Are you sure you want to reject ${teacherName}?`,
      description: 'This teacher will not be able to create courses or sessions.',
      type: 'danger',
      confirmText: 'Yes, Reject',
      onConfirm: async () => {
        try {
          await adminAPI.rejectTeacher(userId);
          showToast('Teacher rejected', 'info');
          loadUsers();
          loadStats();
        } catch (error) {
          showToast(error.response?.data?.error || 'Failed to reject teacher', 'error');
        } finally {
          setConfirmDialog({ isOpen: false });
        }
      },
    });
  };

  const handleDeleteUser = (userId, role, userName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete User',
      message: `Are you sure you want to delete ${userName}?`,
      description: 'This action cannot be undone. All associated data will be permanently removed.',
      type: 'danger',
      confirmText: 'Yes, Delete',
      onConfirm: async () => {
        try {
          if (role === 'teacher') {
            await adminAPI.deleteTeacher(userId);
          } else if (role === 'student') {
            await adminAPI.deleteStudent(userId);
          }
          showToast('User deleted successfully', 'success');
          loadUsers();
          loadStats();
        } catch (error) {
          showToast(error.response?.data?.error || 'Failed to delete user', 'error');
        } finally {
          setConfirmDialog({ isOpen: false });
        }
      },
    });
  };

  // Course code validation regex (alphanumeric, 2-10 chars, can include hyphens)
  const courseCodeRegex = /^[A-Z0-9][A-Z0-9-]{1,9}$/i;

  // Validate form
  const validateCourseForm = () => {
    const errors = {};

    // Course code validation
    if (!courseCode.trim()) {
      errors.courseCode = 'Course code is required';
    } else if (!courseCodeRegex.test(courseCode.trim())) {
      errors.courseCode = 'Course code must be 2-10 alphanumeric characters (hyphens allowed)';
    }

    // Course name validation
    if (!courseName.trim()) {
      errors.courseName = 'Course name is required';
    } else if (courseName.trim().length < 3) {
      errors.courseName = 'Course name must be at least 3 characters';
    } else if (courseName.trim().length > 100) {
      errors.courseName = 'Course name must be less than 100 characters';
    }

    // Teacher validation
    if (!selectedTeacherId) {
      errors.teacherId = 'Please select a teacher';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Check if form is valid for submit button state
  const isFormValid = useMemo(() => {
    return (
      courseCode.trim().length >= 2 &&
      courseCodeRegex.test(courseCode.trim()) &&
      courseName.trim().length >= 3 &&
      selectedTeacherId
    );
  }, [courseCode, courseName, selectedTeacherId]);

  const handleCreateCourse = async (e) => {
    e.preventDefault();

    if (!validateCourseForm()) {
      return;
    }

    setCreatingCourse(true);
    try {
      await adminAPI.createCourse({
        course_code: courseCode.trim().toUpperCase(),
        course_name: courseName.trim(),
        // teacher_id should be the Mongo ObjectId string, not a number
        teacher_id: selectedTeacherId,
      });

      showToast('Course created successfully!', 'success');

      // Reset form
      setCourseCode('');
      setCourseName('');
      setSelectedTeacherId('');
      setFormErrors({});

      // Refresh courses list and stats
      await Promise.all([loadCourses(), loadStats()]);
    } catch (error) {
      const serverError = error.response?.data?.error || '';
      const status = error.response?.status;

      // Handle specific error messages
      if (status === 409 || serverError.toLowerCase().includes('already exists') || serverError.toLowerCase().includes('duplicate')) {
        setFormErrors({ courseCode: 'A course with this code already exists' });
        showToast('Course code already exists. Please use a different code.', 'error');
      } else if (serverError.toLowerCase().includes('teacher') && serverError.toLowerCase().includes('not approved')) {
        setFormErrors({ teacherId: 'Selected teacher is not approved' });
        showToast('The selected teacher is not approved yet.', 'error');
      } else if (serverError.toLowerCase().includes('teacher') && serverError.toLowerCase().includes('not found')) {
        setFormErrors({ teacherId: 'Selected teacher not found' });
        showToast('The selected teacher was not found.', 'error');
      } else {
        showToast(serverError || 'Failed to create course. Please try again.', 'error');
      }
    } finally {
      setCreatingCourse(false);
    }
  };

  // Clear field error when user starts typing
  const handleFieldChange = (setter, field) => (e) => {
    setter(e.target.value);
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  // Edit Course handlers
  const openEditModal = (course) => {
    setEditingCourse(course);
    setEditCourseName(course.course_name);
    setEditTeacherId(course.teacher?.id?.toString() || '');
    setEditFormErrors({});
  };

  const closeEditModal = () => {
    setEditingCourse(null);
    setEditCourseName('');
    setEditTeacherId('');
    setEditFormErrors({});
  };

  const validateEditForm = () => {
    const errors = {};

    if (!editCourseName.trim()) {
      errors.courseName = 'Course name is required';
    } else if (editCourseName.trim().length < 3) {
      errors.courseName = 'Course name must be at least 3 characters';
    } else if (editCourseName.trim().length > 100) {
      errors.courseName = 'Course name must be less than 100 characters';
    }

    if (!editTeacherId) {
      errors.teacherId = 'Please select a teacher';
    }

    setEditFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleUpdateCourse = async (e) => {
    e.preventDefault();

    if (!validateEditForm()) return;

    setSavingCourse(true);
    try {
      await adminAPI.updateCourse(editingCourse.id, {
        course_name: editCourseName.trim(),
        // teacher_id should be sent as the ObjectId string
        teacher_id: editTeacherId,
      });

      showToast('Course updated successfully!', 'success');
      closeEditModal();
      await loadCourses();
    } catch (error) {
      const serverError = error.response?.data?.error || '';

      if (serverError.toLowerCase().includes('teacher') && serverError.toLowerCase().includes('not approved')) {
        setEditFormErrors({ teacherId: 'Selected teacher is not approved' });
        showToast('The selected teacher is not approved yet.', 'error');
      } else if (serverError.toLowerCase().includes('teacher') && serverError.toLowerCase().includes('not found')) {
        setEditFormErrors({ teacherId: 'Selected teacher not found' });
        showToast('The selected teacher was not found.', 'error');
      } else {
        showToast(serverError || 'Failed to update course. Please try again.', 'error');
      }
    } finally {
      setSavingCourse(false);
    }
  };

  const showToast = (message, type) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const allTeachers = users.filter((u) => u.role === 'teacher');
  const allStudents = users.filter((u) => u.role === 'student');

  // Filtered users based on role filter
  const filteredUsers = useMemo(() => {
    if (roleFilter === 'teacher') return allTeachers;
    if (roleFilter === 'student') return allStudents;
    return users;
  }, [users, roleFilter, allTeachers, allStudents]);

  // User details modal handlers
  const openUserDetails = (userToView) => {
    setViewingUser(userToView);
  };

  const closeUserDetails = () => {
    setViewingUser(null);
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
        confirmText={confirmDialog.confirmText}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false })}
      />

      <div className="container">
        {/* Stats Cards */}
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon users">
                <i className="ri-group-line"></i>
              </div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_users || 0}</div>
                <div className="stat-label">Total Users</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon teachers">
                <i className="ri-user-star-line"></i>
              </div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_teachers || 0}</div>
                <div className="stat-label">Teachers</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon students">
                <i className="ri-graduation-cap-line"></i>
              </div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_students || 0}</div>
                <div className="stat-label">Students</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon courses">
                <i className="ri-book-line"></i>
              </div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_courses || 0}</div>
                <div className="stat-label">Courses</div>
              </div>
            </div>
          </div>
        )}

        <div className="section">
          <div className="tabs">
            <button className={`tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
              All Users
            </button>
            <button className={`tab ${activeTab === 'pending' ? 'active' : ''}`} onClick={() => setActiveTab('pending')}>
              Pending Approvals
              {pendingTeachers.length > 0 && (
                <span className="tab-badge">{pendingTeachers.length}</span>
              )}
            </button>
            <button className={`tab ${activeTab === 'courses' ? 'active' : ''}`} onClick={() => setActiveTab('courses')}>
              Courses
            </button>
            <button className={`tab ${activeTab === 'create-course' ? 'active' : ''}`} onClick={() => setActiveTab('create-course')}>
              <i className="ri-add-line"></i> Create Course
            </button>
          </div>

          {/* All Users Tab */}
          {activeTab === 'users' && (
            <div className="tab-content active">
              <div className="tab-header-with-filter">
                <h2><i className="ri-group-line"></i> All Users</h2>
                <div className="role-filter">
                  <button
                    className={`filter-btn ${roleFilter === 'all' ? 'active' : ''}`}
                    onClick={() => setRoleFilter('all')}
                  >
                    All ({users.length})
                  </button>
                  <button
                    className={`filter-btn ${roleFilter === 'teacher' ? 'active' : ''}`}
                    onClick={() => setRoleFilter('teacher')}
                  >
                    <i className="ri-user-star-line"></i> Teachers ({allTeachers.length})
                  </button>
                  <button
                    className={`filter-btn ${roleFilter === 'student' ? 'active' : ''}`}
                    onClick={() => setRoleFilter('student')}
                  >
                    <i className="ri-graduation-cap-line"></i> Students ({allStudents.length})
                  </button>
                </div>
              </div>
              {loading ? (
                <div className="loading">Loading users...</div>
              ) : filteredUsers.length > 0 ? (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((u) => (
                      <tr key={u.id}>
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>
                          <span className={`role-badge role-${u.role}`}>{u.role}</span>
                        </td>
                        <td>
                          <span className={`status-badge status-${u.status}`}>{u.status}</span>
                        </td>
                        <td className="actions-cell">
                          {u.role !== 'admin' && (
                            <>
                              <button
                                className="btn btn-icon btn-sm"
                                onClick={() => openUserDetails(u)}
                                title="View details"
                              >
                                <i className="ri-eye-line"></i>
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                onClick={() => handleDeleteUser(u.id, u.role, u.name)}
                                title="Delete user"
                              >
                                <i className="ri-delete-bin-line"></i>
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <i className="ri-group-line"></i>
                  <p>No {roleFilter === 'all' ? 'users' : roleFilter + 's'} found</p>
                </div>
              )}
            </div>
          )}

          {/* Pending Approvals Tab */}
          {activeTab === 'pending' && (
            <div className="tab-content active">
              <h2><i className="ri-user-add-line"></i> Pending Teacher Approvals</h2>
              {loading ? (
                <div className="loading">Loading...</div>
              ) : pendingTeachers.length > 0 ? (
                <div className="enrollment-list">
                  {pendingTeachers.map((teacher) => (
                    <div key={teacher.id} className="enrollment-card">
                      <div className="enrollment-info">
                        <div className="enrollment-student">
                          <i className="ri-user-star-line"></i> {teacher.name}
                        </div>
                        <div className="enrollment-course">{teacher.email}</div>
                        <div className="enrollment-date">
                          Registered: {new Date(teacher.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="enrollment-actions">
                        <button className="btn btn-success" onClick={() => handleApproveTeacher(teacher.id)}>
                          <i className="ri-check-line"></i> Approve
                        </button>
                        <button className="btn btn-danger" onClick={() => handleRejectTeacher(teacher.id, teacher.name)}>
                          <i className="ri-close-line"></i> Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-user-add-line"></i>
                  <p>No pending teacher approvals</p>
                </div>
              )}
            </div>
          )}

          {/* Courses Tab */}
          {activeTab === 'courses' && (
            <div className="tab-content active">
              <h2><i className="ri-book-line"></i> All Courses</h2>
              {loading ? (
                <div className="loading">Loading courses...</div>
              ) : courses.length > 0 ? (
                <div className="courses-grid">
                  {courses.map((course) => (
                    <div key={course.id} className="course-card">
                      <div className="course-header">
                        <div className="course-code">{course.course_code}</div>
                        <button
                          className="btn btn-icon btn-sm"
                          onClick={() => openEditModal(course)}
                          title="Edit course"
                        >
                          <i className="ri-edit-line"></i>
                        </button>
                      </div>
                      <div className="course-name">{course.course_name}</div>
                      <div className="course-info">
                        <span><i className="ri-user-line"></i> {course.teacher?.name || 'Unassigned'}</span>
                        <span><i className="ri-group-line"></i> {course.student_count || 0} students</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <i className="ri-book-line"></i>
                  <p>No courses found</p>
                  <button className="btn btn-primary mt-3" onClick={() => setActiveTab('create-course')}>
                    <i className="ri-add-line"></i> Create First Course
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Create Course Tab */}
          {activeTab === 'create-course' && (
            <div className="tab-content active">
              <h2><i className="ri-add-circle-line"></i> Create New Course</h2>

              <div className="create-session-form">
                <form onSubmit={handleCreateCourse}>
                  <div className="form-group">
                    <label htmlFor="courseCode">
                      Course Code <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      id="courseCode"
                      value={courseCode}
                      onChange={handleFieldChange(setCourseCode, 'courseCode')}
                      placeholder="e.g., CS101, MATH-201"
                      disabled={creatingCourse}
                      className={formErrors.courseCode ? 'input-error' : ''}
                      maxLength={10}
                    />
                    {formErrors.courseCode && (
                      <p className="field-error">
                        <i className="ri-error-warning-line"></i> {formErrors.courseCode}
                      </p>
                    )}
                    <p className="field-hint">2-10 alphanumeric characters, hyphens allowed</p>
                  </div>

                  <div className="form-group">
                    <label htmlFor="courseName">
                      Course Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      id="courseName"
                      value={courseName}
                      onChange={handleFieldChange(setCourseName, 'courseName')}
                      placeholder="e.g., Introduction to Computer Science"
                      disabled={creatingCourse}
                      className={formErrors.courseName ? 'input-error' : ''}
                      maxLength={100}
                    />
                    {formErrors.courseName && (
                      <p className="field-error">
                        <i className="ri-error-warning-line"></i> {formErrors.courseName}
                      </p>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="teacherId">
                      Assign Teacher <span className="required">*</span>
                    </label>
                    <select
                      id="teacherId"
                      value={selectedTeacherId}
                      onChange={handleFieldChange(setSelectedTeacherId, 'teacherId')}
                      disabled={creatingCourse}
                      className={formErrors.teacherId ? 'input-error' : ''}
                    >
                      <option value="">Select a teacher...</option>
                      {approvedTeachers.map((teacher) => (
                        <option key={teacher.id} value={teacher.id}>
                          {teacher.name} ({teacher.email})
                        </option>
                      ))}
                    </select>
                    {formErrors.teacherId && (
                      <p className="field-error">
                        <i className="ri-error-warning-line"></i> {formErrors.teacherId}
                      </p>
                    )}
                    {approvedTeachers.length === 0 && !loading && (
                      <p className="field-hint warning">
                        <i className="ri-alert-line"></i> No approved teachers available. Please approve a teacher first.
                      </p>
                    )}
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary full-width"
                    disabled={creatingCourse || !isFormValid || approvedTeachers.length === 0}
                  >
                    {creatingCourse ? (
                      <>
                        <i className="ri-loader-4-line ri-spin"></i> Creating Course...
                      </>
                    ) : (
                      <>
                        <i className="ri-add-line"></i> Create Course
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Course Modal */}
      {editingCourse && (
        <div className="confirm-overlay" onClick={closeEditModal}>
          <div className="confirm-dialog edit-modal" onClick={(e) => e.stopPropagation()}>
            <div className="confirm-header info">
              <div className="confirm-icon">
                <i className="ri-edit-line"></i>
              </div>
              <h3 className="confirm-title">Edit Course</h3>
            </div>

            <form onSubmit={handleUpdateCourse}>
              <div className="confirm-body">
                <div className="form-group">
                  <label>Course Code</label>
                  <input
                    type="text"
                    value={editingCourse.course_code}
                    disabled
                    className="input-disabled"
                  />
                  <p className="field-hint">Course code cannot be changed</p>
                </div>

                <div className="form-group">
                  <label htmlFor="editCourseName">
                    Course Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    id="editCourseName"
                    value={editCourseName}
                    onChange={(e) => {
                      setEditCourseName(e.target.value);
                      if (editFormErrors.courseName) {
                        setEditFormErrors(prev => ({ ...prev, courseName: null }));
                      }
                    }}
                    placeholder="e.g., Introduction to Computer Science"
                    disabled={savingCourse}
                    className={editFormErrors.courseName ? 'input-error' : ''}
                    maxLength={100}
                  />
                  {editFormErrors.courseName && (
                    <p className="field-error">
                      <i className="ri-error-warning-line"></i> {editFormErrors.courseName}
                    </p>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="editTeacherId">
                    Assigned Teacher <span className="required">*</span>
                  </label>
                  <select
                    id="editTeacherId"
                    value={editTeacherId}
                    onChange={(e) => {
                      setEditTeacherId(e.target.value);
                      if (editFormErrors.teacherId) {
                        setEditFormErrors(prev => ({ ...prev, teacherId: null }));
                      }
                    }}
                    disabled={savingCourse}
                    className={editFormErrors.teacherId ? 'input-error' : ''}
                  >
                    <option value="">Select a teacher...</option>
                    {approvedTeachers.map((teacher) => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.name} ({teacher.email})
                      </option>
                    ))}
                  </select>
                  {editFormErrors.teacherId && (
                    <p className="field-error">
                      <i className="ri-error-warning-line"></i> {editFormErrors.teacherId}
                    </p>
                  )}
                </div>
              </div>

              <div className="confirm-footer">
                <button
                  type="button"
                  className="confirm-btn cancel"
                  onClick={closeEditModal}
                  disabled={savingCourse}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="confirm-btn confirm info"
                  disabled={savingCourse || !editCourseName.trim() || !editTeacherId}
                >
                  {savingCourse ? (
                    <>
                      <i className="ri-loader-4-line ri-spin"></i> Saving...
                    </>
                  ) : (
                    <>
                      <i className="ri-save-line"></i> Save Changes
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Details Modal */}
      {viewingUser && (
        <div className="confirm-overlay" onClick={closeUserDetails}>
          <div className="confirm-dialog user-details-modal" onClick={(e) => e.stopPropagation()}>
            <div className={`confirm-header ${viewingUser.role === 'teacher' ? 'info' : 'success'}`}>
              <div className="confirm-icon">
                <i className={viewingUser.role === 'teacher' ? 'ri-user-star-line' : 'ri-graduation-cap-line'}></i>
              </div>
              <h3 className="confirm-title">
                {viewingUser.role === 'teacher' ? 'Teacher' : 'Student'} Details
              </h3>
            </div>

            <div className="confirm-body user-details-body">
              {/* Basic Info Section */}
              <div className="user-details-section">
                <h4 className="section-title">
                  <i className="ri-user-line"></i> Basic Information
                </h4>
                <div className="user-details-grid">
                  <div className="detail-item">
                    <span className="detail-label">Name</span>
                    <span className="detail-value">{viewingUser.name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Email</span>
                    <span className="detail-value">{viewingUser.email}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Role</span>
                    <span className={`role-badge role-${viewingUser.role}`}>
                      {viewingUser.role}
                    </span>
                  </div>
                  {viewingUser.role === 'teacher' && (
                    <div className="detail-item">
                      <span className="detail-label">Status</span>
                      <span className={`status-badge status-${viewingUser.status}`}>
                        {viewingUser.status}
                      </span>
                    </div>
                  )}
                  {viewingUser.created_at && (
                    <div className="detail-item">
                      <span className="detail-label">Registered</span>
                      <span className="detail-value">
                        {new Date(viewingUser.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Courses Section */}
              <div className="user-details-section">
                <h4 className="section-title">
                  <i className="ri-book-line"></i>
                  {viewingUser.role === 'teacher' ? ' Courses Teaching' : ' Enrolled Courses'}
                </h4>
                {viewingUser.courses && viewingUser.courses.length > 0 ? (
                  <div className="user-courses-list">
                    {viewingUser.courses.map((course) => (
                      <div key={course.id} className="user-course-item">
                        <div className="course-code-badge">{course.course_code}</div>
                        <div className="course-details">
                          <span className="course-name-text">{course.course_name}</span>
                          {viewingUser.role === 'teacher' && course.student_count !== undefined && (
                            <span className="course-student-count">
                              <i className="ri-group-line"></i> {course.student_count} student{course.student_count !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-courses-message">
                    <i className="ri-inbox-line"></i>
                    <span>
                      {viewingUser.role === 'teacher'
                        ? 'Not teaching any courses yet'
                        : 'Not enrolled in any courses yet'}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="confirm-footer">
              <button
                type="button"
                className="confirm-btn cancel full-width-btn"
                onClick={closeUserDetails}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
