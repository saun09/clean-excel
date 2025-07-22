from flask import Blueprint, request, jsonify
import os
import pandas as pd
import numpy as np
from settings import Config
from analysis import comparative_analysis
from utils.json_utils import convert_nan_to_none
import json

comparative_bp = Blueprint('comparative_bp', __name__)

@comparative_bp.route('/api/load-comparative-options', methods=['POST'])
def load_comparative_options():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        # Convert Month column to datetime to extract years
        df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
        df['year'] = df['Month'].dt.year
        
        # Initialize options dictionary
        options = {
            'years': [],
            'hscodes': [],
            'item_descriptions': []
        }

        # Populate years from Month column
        if 'year' in df.columns:
            years = df['year'].dropna().unique().tolist()
            options['years'] = sorted([int(year) for year in years if not pd.isna(year)])

        # Populate HS codes - using 'CTH_HSCODE' column
        if 'CTH_HSCODE' in df.columns:
            hscodes = df['CTH_HSCODE'].dropna().unique().tolist()
            options['hscodes'] = sorted([str(code) for code in hscodes])

        # Populate item descriptions - using 'Item_Description' column
        if 'Item_Description' in df.columns:
            items = df['Item_Description'].dropna().unique().tolist()
            options['item_descriptions'] = sorted(items)
        elif 'Item_Description' in df.columns:
            # Fallback to regular Item_Description if cluster column doesn't exist
            items = df['Item_Description'].dropna().unique().tolist()
            options['item_descriptions'] = sorted(items)

        print(f" Comparative options loaded for {len(df)} records")
        print(f"Available columns: {df.columns.tolist()}")
        print(f"Options: {options}")

        return jsonify({
            'success': True,
            'options': options,
            'message': 'Comparative analysis options loaded successfully'
        })
    except Exception as e:
        print(f" Error loading comparative options: {str(e)}")
        return jsonify({'error': f'Failed to load comparative options: {str(e)}'}), 500

@comparative_bp.route('/api/perform-comparative-analysis', methods=['POST'])
def perform_comparative_analysis():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)

        # Extract parameters
        selected_years = data.get('selected_years', [])
        time_period_type = data.get('time_period_type', 'quarter')
        selected_quarter_or_month = data.get('selected_quarter_or_month', 'Q1')
        selected_hscode = data.get('selected_hscode')
        item_description_1 = data.get('item_description_1')
        item_description_2 = data.get('item_description_2')

        # Validate required parameters
        if not selected_years:
            return jsonify({'error': 'Please select at least one year'}), 400
        if not selected_hscode:
            return jsonify({'error': 'Please select an HS Code'}), 400
        if not item_description_1:
            return jsonify({'error': 'Please select Item Description 1'}), 400
        if not item_description_2:
            return jsonify({'error': 'Please select Item Description 2'}), 400

        print(f"Performing comparative analysis:")
        print(f"Years: {selected_years}")
        print(f"Time Period: {time_period_type} - {selected_quarter_or_month}")
        print(f"HS Code: {selected_hscode}")
        print(f"Item 1: {item_description_1}")
        print(f"Item 2: {item_description_2}")

        # Determine which column to use for item descriptions
        item_col = 'Item_Description' if 'Item_Description' in df.columns else 'Item_Description'

        # Perform comparative analysis for both items
        result_item1 = comparative_analysis(
            df.copy(), 
            selected_years, 
            time_period_type, 
            selected_quarter_or_month, 
            selected_hscode, 
            item_description_1,
            quantity_col='Quantity',
            month_col='Month'
        )
        
        result_item2 = comparative_analysis(
            df.copy(), 
            selected_years, 
            time_period_type, 
            selected_quarter_or_month, 
            selected_hscode, 
            item_description_2,
            quantity_col='Quantity',
            month_col='Month'
        )

        # Add item names to results for identification
        result_item1['item'] = item_description_1
        result_item2['item'] = item_description_2

        # Combine results
        combined_results = pd.concat([result_item1, result_item2], ignore_index=True)

        # Create comparison summary
        summary = {
            'item_1': {
                'name': item_description_1,
                'total_quantity': float(result_item1['Quantity'].sum()) if not result_item1.empty else 0,
                'years_data': result_item1.to_dict('records') if not result_item1.empty else []
            },
            'item_2': {
                'name': item_description_2,
                'total_quantity': float(result_item2['Quantity'].sum()) if not result_item2.empty else 0,
                'years_data': result_item2.to_dict('records') if not result_item2.empty else []
            }
        }

        # Clean NaN values
        cleaned_results = convert_nan_to_none({
            'summary': summary,
            'combined_data': combined_results.to_dict('records'),
            'parameters': {
                'years': selected_years,
                'time_period': f"{time_period_type} - {selected_quarter_or_month}",
                'hscode': selected_hscode,
                'items_compared': [item_description_1, item_description_2]
            }
        })

        json_str = json.dumps(cleaned_results, default=str)
        cleaned_results = json.loads(json_str)

        print(f"Comparative analysis completed")
        print(f"Item 1 total: {summary['item_1']['total_quantity']}")
        print(f"Item 2 total: {summary['item_2']['total_quantity']}")

        return jsonify({
            'success': True,
            'results': cleaned_results,
            'message': 'Comparative analysis completed successfully'
        })

    except Exception as e:
        print(f"Comparative analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Comparative analysis failed: {str(e)}'
        }), 500