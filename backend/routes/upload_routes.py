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


print("upload_routes.py: All imports done")
upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        original_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"uploaded_{timestamp}_{original_name}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)

        preview_data = generate_preview_data(file_path)

        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'preview': preview_data
        })

    return jsonify({'error': 'File type not allowed'}), 400

@upload_bp.route('/api/standardize', methods=['POST'])
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
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        df_cleaned = clean_standardize_data(df)
        
        save_df_to_session("cleaned_df", df_cleaned)
        print("✅ Stored df in session:", session.get("cleaned_df") is not None)
        print("🔑 Session keys:", list(session.keys()))
       
        print("✅✅ After saving: Session keys:", list(session.keys()))


        cleaned_filename = f"cleaned_{filename.rsplit('.', 1)[0]}.csv"
        cleaned_file_path = os.path.join(Config.UPLOAD_FOLDER, cleaned_filename)
        df_cleaned.to_csv(cleaned_file_path, index=False)

        return jsonify({'message': 'Data standardized successfully', 'cleaned_filename': cleaned_filename})
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@upload_bp.route('/api/headers/<filename>', methods=['GET'])
def get_column_headers(filename):
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        return jsonify({'headers': list(df.columns)})
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 500

@upload_bp.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, as_attachment=True)