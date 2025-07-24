""" print("importing flask")
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import os
from settings import Config

print("importing upload_bp")
from routes.upload_routes import upload_bp

print("importing clustering_bp")
from routes.clustering_routes import clustering_bp

print("importing export_bp")
from routes.export_routes import export_bp

print("importing filter_bp")
from routes.filter_routes import filter_bp

print("importing forecast_bp")
from routes.forecast_routes import forecast_bp

print("importing cosine_bp")
from routes.cosine_routes import cosine_bp

from routes.comparative_routes import comparative_bp
print("importing comparative_bp")

from routes.Company_Analysis_routes import company_bp
print("importing company_analysis_bp")

from routes.Cluster_Analysis_routes import cluster_analysis_bp
print("importing cluster_analysis_bp")

from routes.auth_routes import login_bp
print("importing login_bp")

app = Flask(__name__)

load_dotenv()  # Load from .env

app.secret_key = os.getenv('FLASK_SECRET', 'fallbacksecret')  # needed for sessions

app.config.from_object(Config)
Config.init_app(app)
print("Config loaded")


CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # for local testing
            "https://clean-excel-og7bgez01-saundarya-s-projects.vercel.app"  # for Vercel
        ]
    }
})
Session(app)

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(clustering_bp)
app.register_blueprint(export_bp)
app.register_blueprint(filter_bp)
app.register_blueprint(forecast_bp)
app.register_blueprint(cosine_bp)
app.register_blueprint(comparative_bp)
app.register_blueprint(company_bp)
app.register_blueprint(cluster_analysis_bp)

if __name__ == '__main__':
    app.run(debug=True)

 """

print("importing flask")
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import os
from settings import Config

print("importing upload_bp")
from routes.upload_routes import upload_bp

print("importing clustering_bp")
from routes.clustering_routes import clustering_bp

print("importing export_bp")
from routes.export_routes import export_bp

print("importing filter_bp")
from routes.filter_routes import filter_bp

# Temporarily comment out forecast routes if they cause issues
print("importing forecast_bp")
try:
    from routes.forecast_routes import forecast_bp
    FORECAST_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import forecast_routes: {e}")
    FORECAST_AVAILABLE = False

print("importing cosine_bp")
from routes.cosine_routes import cosine_bp

from routes.comparative_routes import comparative_bp
print("importing comparative_bp")

from routes.Company_Analysis_routes import company_bp
print("importing company_analysis_bp")

from routes.Cluster_Analysis_routes import cluster_analysis_bp
print("importing cluster_analysis_bp")

from routes.auth_routes import login_bp
print("importing login_bp")

app = Flask(__name__)

load_dotenv()  # Load from .env

app.secret_key = os.getenv('FLASK_SECRET', 'fallbacksecret')  # needed for sessions

app.config.from_object(Config)
Config.init_app(app)
print("Config loaded")

CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # for local testing
            "https://clean-excel-og7bgez01-saundarya-s-projects.vercel.app"  # for Vercel
        ]
    }
})
Session(app)

# Health check route for deployment
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Clean Excel API is running'}, 200

@app.route('/')
def home():
    return {
        'message': 'Clean Excel API is running',
        'status': 'success',
        'endpoints': ['/health', '/api/upload', '/api/clustering', '/api/export']
    }, 200

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(clustering_bp)
app.register_blueprint(export_bp)
app.register_blueprint(filter_bp)

# Only register forecast blueprint if it imported successfully
if FORECAST_AVAILABLE:
    app.register_blueprint(forecast_bp)
    print("Forecast routes registered")
else:
    print("Forecast routes skipped due to import error")

app.register_blueprint(cosine_bp)
app.register_blueprint(comparative_bp)
app.register_blueprint(company_bp)
app.register_blueprint(cluster_analysis_bp)

print("All blueprints registered successfully")

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    # For production deployment (when imported by gunicorn)
    print("App imported by gunicorn for production deployment")