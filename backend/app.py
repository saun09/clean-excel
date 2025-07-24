print("importing flask")
from flask import Flask, request, jsonify
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

# ADD THESE LINES FOR TIMEOUT HANDLING
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Increase file size limit if needed
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB (increased from 100MB)

app.config.from_object(Config)
Config.init_app(app)
print("Config loaded")

# CORS configuration - FIXED VERSION
CORS(app, 
     supports_credentials=True,
     origins=["http://localhost:3000", "https://clean-excel.vercel.app", "https://*.vercel.app"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
     expose_headers=["Content-Type", "Authorization"])

# Add these CORS handlers
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        origin = request.headers.get('Origin')
        
        # Allow specific origins or any vercel.app subdomain
        if origin and (origin in ["http://localhost:3000", "https://clean-excel.vercel.app"] or 
                      origin.endswith(".vercel.app")):
            response.headers.add("Access-Control-Allow-Origin", origin)
        else:
            response.headers.add("Access-Control-Allow-Origin", "https://clean-excel.vercel.app")
            
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,Origin,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    
    # Set specific origin if it's in our allowed list
    if origin and (origin in ["http://localhost:3000", "https://clean-excel.vercel.app"] or 
                  origin.endswith(".vercel.app")):
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        # Fallback for any other requests
        response.headers.add('Access-Control-Allow-Origin', 'https://clean-excel.vercel.app')
        
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept,Origin,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

Session(app)

# Add a test endpoint to verify CORS is working
@app.route('/api/test-cors', methods=['GET', 'POST', 'OPTIONS'])
def test_cors():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        "message": "CORS is working!", 
        "origin": request.headers.get('Origin'),
        "method": request.method
    })

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