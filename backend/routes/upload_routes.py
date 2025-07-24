print("upload_routes.py: STARTING")
from flask import Blueprint, request, jsonify, send_file, session
import os
from datetime import datetime
from werkzeug.utils import secure_filename

print("upload_routes.py: before Config import")

from settings import Config

import utils

print("upload_routes.py: before file_utils import")
from utils.files_utils import allowed_file, generate_preview_data

print("upload_routes.py: before clean_standardize_data")
from data_cleaning import clean_standardize_data

print("upload_routes.py: before save_df_to_session")
from utils.session_utils import save_df_to_session
import pandas as pd

# --------------- ADDED FOR TIMEOUT HANDLING ---------------
import signal
from functools import wraps
import time

def timeout_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "timeout" in str(e).lower():
                return jsonify({"error": "Request timeout - file too large or processing taking too long"}), 408
            raise e
    return wrapper
# --------------- END TIMEOUT HANDLING ---------------

print("upload_routes.py: All imports done")
upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/api/upload', methods=['POST'])
# --------------- ADDED TIMEOUT DECORATOR ---------------
@timeout_handler
# --------------- END TIMEOUT DECORATOR ---------------
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # --------------- ADDED PROGRESS LOGGING ---------------
        print(f"Processing file: {file.filename}, size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
        # --------------- END PROGRESS LOGGING ---------------
        
        original_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"uploaded_{timestamp}_{original_name}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # --------------- ADDED PROGRESS LOGGING ---------------
        print("Saving file to disk...")
        # --------------- END PROGRESS LOGGING ---------------
        file.save(file_path)

        # --------------- ADDED PROGRESS LOGGING ---------------
        print("Generating preview data...")
        # --------------- END PROGRESS LOGGING ---------------
        preview_data = generate_preview_data(file_path)

        # --------------- ADDED PROGRESS LOGGING ---------------
        print("Upload completed successfully")
        # --------------- END PROGRESS LOGGING ---------------
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'preview': preview_data
        })

    return jsonify({'error': 'File type not allowed'}), 400

@upload_bp.route('/api/standardize', methods=['POST'])
# --------------- ADDED TIMEOUT DECORATOR ---------------
@timeout_handler
# --------------- END TIMEOUT DECORATOR ---------------
def standardize_data():
    
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400
    print("UPLOAD_FOLDER:", Config.UPLOAD_FOLDER)
    print("File path:", os.path.join(Config.UPLOAD_FOLDER, filename))
    print("Exists:", os.path.exists(os.path.join(Config.UPLOAD_FOLDER, filename)))

    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': f'File not found: {filename}'}), 404

    try:
        # --------------- ADDED PROGRESS LOGGING ---------------
        print("Starting data standardization...")
        start_time = time.time()
        # --------------- END PROGRESS LOGGING ---------------
        
        if filename.endswith('.csv'):
            # --------------- ADDED CHUNKED READING FOR LARGE FILES ---------------
            print("Reading CSV file...")
            try:
                df = pd.read_csv(file_path)
            except MemoryError:
                # If file is too large, try reading in chunks
                print("File too large, reading in chunks...")
                chunks = []
                for chunk in pd.read_csv(file_path, chunksize=10000):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            # --------------- END CHUNKED READING ---------------
        else:
            print("Reading Excel file...")
            df = pd.read_excel(file_path)
        
        # --------------- ADDED PROGRESS LOGGING ---------------
        print(f"File loaded, shape: {df.shape}")
        print("Cleaning and standardizing data...")
        # --------------- END PROGRESS LOGGING ---------------
            
        df_cleaned = clean_standardize_data(df)
        
        # --------------- ADDED PROGRESS LOGGING ---------------
        print("Data cleaned, saving to session...")
        # --------------- END PROGRESS LOGGING ---------------
        
        save_df_to_session("cleaned_df", df_cleaned)
        print(" Stored df in session:", session.get("cleaned_df") is not None)
        print(" Session keys:", list(session.keys()))
       
        print("After saving: Session keys:", list(session.keys()))

        # --------------- ADDED PROGRESS LOGGING ---------------
        print("Saving cleaned file to disk...")
        # --------------- END PROGRESS LOGGING ---------------

        cleaned_filename = f"cleaned_{filename.rsplit('.', 1)[0]}.csv"
        cleaned_file_path = os.path.join(Config.UPLOAD_FOLDER, cleaned_filename)
        df_cleaned.to_csv(cleaned_file_path, index=False)

        # --------------- ADDED PROGRESS LOGGING ---------------
        end_time = time.time()
        print(f"Standardization completed in {end_time - start_time:.2f} seconds")
        # --------------- END PROGRESS LOGGING ---------------

        return jsonify({'message': 'Data standardized successfully', 'cleaned_filename': cleaned_filename})
    except Exception as e:
        # --------------- ENHANCED ERROR HANDLING ---------------
        print(f"Error during standardization: {str(e)}")
        if "timeout" in str(e).lower() or "memory" in str(e).lower():
            return jsonify({'error': f'File too large or processing timeout: {str(e)}'}), 408
        # --------------- END ENHANCED ERROR HANDLING ---------------
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@upload_bp.route('/api/headers/<filename>', methods=['GET'])
# --------------- ADDED TIMEOUT DECORATOR ---------------
@timeout_handler
# --------------- END TIMEOUT DECORATOR ---------------
def get_column_headers(filename):
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    try:
        # --------------- ADDED CHUNKED READING FOR HEADERS ---------------
        if filename.endswith('.csv'):
            # Only read first few rows to get headers for large files
            df = pd.read_csv(file_path, nrows=1)
        else:
            df = pd.read_excel(file_path, nrows=1)
        # --------------- END CHUNKED READING FOR HEADERS ---------------
        return jsonify({'headers': list(df.columns)})
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 500

@upload_bp.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, as_attachment=True)