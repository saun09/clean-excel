""" import os
print("Loaded settings.py")

class Config:
    SECRET_KEY = 'your-secret'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # ← absolute path
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # should be False for localhost

    
    @staticmethod
    def init_app(app):
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
 """

import os
print("Loaded settings.py")

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET', 'your-secret')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # ← absolute path
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_COOKIE_SAMESITE = "None"  # Required for cross-origin cookies
    SESSION_COOKIE_SECURE = True  # Required for HTTPS in production
    SESSION_COOKIE_HTTPONLY = True  # Security best practice
    
    @staticmethod
    def init_app(app):
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # False for localhost
    SESSION_COOKIE_SAMESITE = "Lax"

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # True for HTTPS
    SESSION_COOKIE_SAMESITE = "None"  # Required for cross-origin

# Choose config based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Use production config by default on Render
Config = config.get(os.getenv('FLASK_ENV', 'production'))