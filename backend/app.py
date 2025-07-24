print("importing flask")
from flask import Flask, request
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

# Dynamic CORS function to handle Vercel's changing URLs
def is_allowed_origin(origin):
    if not origin:
        return False
    
    allowed_origins = [
        "http://localhost:3000",
        "https://clean-excel.vercel.app"
    ]
    
    # Check exact matches first
    if origin in allowed_origins:
        return True
    
    # Allow any Vercel preview deployment
    if origin.endswith(".vercel.app") and "saundarya-s-projects" in origin:
        return True
        
    return False

# CORS configuration with dynamic origin checking
CORS(app, 
     supports_credentials=True,
     origins="*",  # Allow all origins temporarily
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Access-Control-Allow-Origin"])


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