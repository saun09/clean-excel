from flask import Blueprint, request, jsonify
import os
import pandas as pd
import numpy as np
from settings import Config
from analysis import perform_trade_analysis
from utils.json_utils import convert_nan_to_none
import json

filter_bp = Blueprint('filter_bp', __name__)

@filter_bp.route('/api/load-filter-options', methods=['POST'])
def load_filter_options():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        options = {
            'trade_types': [],
            'importer_cities': [],
            'supplier_countries': [],
            'numeric_columns': [],
            'years': [],
            'hscodes': [],
            'item_descriptions': []
        }

        # Populate options...
        # (Same implementation as original)

        return jsonify({
            'success': True,
            'options': options,
            'message': 'Filter options loaded successfully'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load filter options: {str(e)}'}), 500

@filter_bp.route('/api/filter-data', methods=['POST'])
def filter_data():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)

        # Filter implementation...
        # (Same as original)

        preview = df.head(20).replace({np.nan: None}).to_dict(orient='records')

        return jsonify({
            'success': True,
            'data': preview,
            'message': f'Filter applied successfully. Found {len(preview)} records.',
            'filters_applied': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Filter error: {str(e)}'
        }), 500

@filter_bp.route('/api/analyze-filtered', methods=['POST'])
def analyze_filtered_data():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)

        # Filter implementation...
        # (Same as original)

        value_col = data.get('value_col')
        analysis_results = perform_trade_analysis(
            df.copy(),
            product_col='Item_Description_cluster',
            quantity_col='Quantity',
            value_col=value_col,
            importer_col='Importer_City_State',
            supplier_col='Country_of_Origin'
        )

        cleaned_results = convert_nan_to_none(analysis_results)
        json_str = json.dumps(cleaned_results, default=str)
        cleaned_results = json.loads(json_str)

        return jsonify({
            'success': True,
            'results': cleaned_results,
            'message': f'Analyzed {len(df)} records'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500