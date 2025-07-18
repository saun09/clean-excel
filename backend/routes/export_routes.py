from flask import Blueprint, request, jsonify
import os
import pandas as pd
from settings import Config
from export_excel import create_colored_excel

export_bp = Blueprint('export_bp', __name__)

@export_bp.route('/api/export-colored-excel', methods=['POST'])
def export_colored_excel():
    data = request.json
    filename = data.get('filename')
    cluster_column = data.get('cluster_column')

    if not filename or not cluster_column:
        return jsonify({'error': 'Filename and cluster column are required'}), 400

    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        excel_bytes = create_colored_excel(df, cluster_column)
        if excel_bytes is None:
            return jsonify({'error': 'Cluster column not found in file'}), 500

        excel_filename = f"colored_{filename.rsplit('.', 1)[0]}.xlsx"
        excel_path = os.path.join(Config.UPLOAD_FOLDER, excel_filename)
        
        with open(excel_path, 'wb') as f:
            f.write(excel_bytes)

        return jsonify({'message': 'Excel created', 'excel_filename': excel_filename})
    except Exception as e:
        return jsonify({'error': f'Excel generation error: {str(e)}'}), 500