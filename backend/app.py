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

# Updated CORS configuration for production
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
allowed_origins = [frontend_url, "http://localhost:3000"]

# If FRONTEND_URL is not set, allow common Render patterns
if 'FRONTEND_URL' not in os.environ:
    allowed_origins.extend([
        "https://*.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ])

CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": allowed_origins}})
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
    # Production-ready configuration
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Starting Flask app on port {port}")
    print(f"Debug mode: {debug_mode}")
    print(f"Allowed CORS origins: {allowed_origins}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)