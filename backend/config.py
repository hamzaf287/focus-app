"""
Configuration file for Focus Detection App
Contains database connection settings and app configuration
"""

import os

class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'

    # MongoDB settings
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://hamzafaisal18_db_user:Tkj6wEPRhuf1jU2D@focuscheckcluster.zswpzmd.mongodb.net/focus_app?retryWrites=true&w=majority&appName=focuscheckCluster'

    # Session settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds

    # File upload settings
    UPLOAD_FOLDER = 'static/videos'
    REPORTS_FOLDER = 'static/reports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Model settings
    MODEL_PATH = "focus_binary_classifier_finetuned.pth"

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create required directories if they don't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/focus_app_test'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
