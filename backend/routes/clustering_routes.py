from flask import Blueprint, request, jsonify, session
import os
import pandas as pd
import numpy as np
from settings import Config
from clustering import add_cluster_column
from utils.session_utils import save_df_to_session

clustering_bp = Blueprint('clustering_bp', __name__)

@clustering_bp.route('/api/cluster', methods=['POST'])
def cluster_data():
    data = request.json
    column = data.get('column')
    filename = data.get('filename')

    if not column or not filename:
        return jsonify({'error': 'Both filename and column are required'}), 400

    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': f'File not found: {filename}'}), 404

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        df_clustered = add_cluster_column(df, column)
        save_df_to_session(df_clustered)

        clustered_filename = "clustered_data.csv"
        out_path = os.path.join(Config.UPLOAD_FOLDER, clustered_filename)
        df_clustered.to_csv(out_path, index=False)

        preview = df_clustered.head(10).fillna('').to_dict(orient='records')

        return jsonify({
            'message': 'Data clustered successfully',
            'clustered_filename': clustered_filename,
            'preview': preview
        })
    except Exception as e:
        return jsonify({'error': f'Error clustering data: {str(e)}'}), 500

@clustering_bp.route('/api/get-clustered-preview', methods=['POST'])
def get_clustered_preview():
    try:
        data = request.json
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        preview = df.head(20).fillna('').to_dict(orient='records')
        
        return jsonify({
            'success': True,
            'preview': preview,
            'message': 'Preview loaded successfully'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load preview: {str(e)}'}), 500