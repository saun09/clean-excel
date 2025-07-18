from flask import Blueprint, request, jsonify
import os
import pandas as pd
from settings import Config

forecast_bp = Blueprint('forecast_bp', __name__)

@forecast_bp.route('/api/load-forecast-options', methods=['POST'])
def load_forecast_options():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        try:
            df = pd.read_csv(file_path)
        except:
            df = pd.read_excel(file_path)
        
        # Cluster column detection...
        # (Same as original)

        return jsonify({
            'success': True,
            'options': {
                'items': items,
                'value_columns': numeric_cols
            }
        })
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500