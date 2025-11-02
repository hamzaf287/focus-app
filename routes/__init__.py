"""
Routes package
Contains all API route blueprints for the Focus Detection App
"""

from . import auth_routes
from . import admin_routes
from . import teacher_routes
from . import student_routes

__all__ = ['auth_routes', 'admin_routes', 'teacher_routes', 'student_routes']
