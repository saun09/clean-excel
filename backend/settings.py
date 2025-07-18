import os
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
