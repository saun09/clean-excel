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
        
        # Initialize options dictionary
        options = {
            'trade_types': [],
            'importer_cities': [],
            'supplier_countries': [],
            'numeric_columns': [],
            'years': [],
            'hscodes': [],
            'item_descriptions': []
        }

        # Populate trade types - using 'Type' column
        if 'Type' in df.columns:
            options['trade_types'] = sorted(df['Type'].dropna().unique().tolist())

        # Populate importer cities - using 'Importer_City_State' column
        if 'Importer_City_State' in df.columns:
            options['importer_cities'] = sorted(df['Importer_City_State'].dropna().unique().tolist())

        # Populate supplier countries - using 'Country_of_Origin' column
        if 'Country_of_Origin' in df.columns:
            options['supplier_countries'] = sorted(df['Country_of_Origin'].dropna().unique().tolist())

        # Populate numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove index-like columns
        numeric_cols = [col for col in numeric_cols if not col.lower().startswith('unnamed')]
        options['numeric_columns'] = numeric_cols

        # Populate years from 'Month' column
        if 'Month' in df.columns:
            try:
                # Convert Month column to datetime and extract years
                df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
                years = df['Month'].dt.year.dropna().unique().tolist()
                options['years'] = sorted([int(year) for year in years])
            except:
                # Fallback to YEAR column if Month parsing fails
                if 'YEAR' in df.columns:
                    options['years'] = sorted(df['YEAR'].dropna().unique().tolist())
        elif 'YEAR' in df.columns:
            options['years'] = sorted(df['YEAR'].dropna().unique().tolist())

        # Populate HS codes - using 'CTH_HSCODE' column
        if 'CTH_HSCODE' in df.columns:
            options['hscodes'] = sorted(df['CTH_HSCODE'].dropna().astype(str).unique().tolist())

        # Populate item descriptions - using 'Item_Description' column
        if 'Item_Description' in df.columns:
            options['item_descriptions'] = sorted(df['Item_Description'].dropna().unique().tolist())

        print(f" Filter options loaded for {len(df)} records")
        print(f"Available columns: {df.columns.tolist()}")
        print(f"Options: {options}")

        return jsonify({
            'success': True,
            'options': options,
            'message': 'Filter options loaded successfully'
        })
    except Exception as e:
        print(f" Error loading filter options: {str(e)}")
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
        original_count = len(df)

        # Apply filters
        if 'tradeType' in data and data['tradeType']:
            if 'Type' in df.columns:
                df = df[df['Type'].isin(data['tradeType'])]

        if 'importer' in data and data['importer']:
            if 'Importer_City_State' in df.columns:
                df = df[df['Importer_City_State'].isin(data['importer'])]

        if 'supplier' in data and data['supplier']:
            if 'Country_of_Origin' in df.columns:
                df = df[df['Country_of_Origin'].isin(data['supplier'])]

        if 'years' in data and data['years']:
            # Try to filter by year from Month column first
            if 'Month' in df.columns:
                try:
                    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
                    df = df[df['Month'].dt.year.isin([int(y) for y in data['years']])]
                except:
                    # Fallback to YEAR column
                    if 'YEAR' in df.columns:
                        df = df[df['YEAR'].isin([int(y) for y in data['years']])]
            elif 'YEAR' in df.columns:
                df = df[df['YEAR'].isin([int(y) for y in data['years']])]

        if 'hscode' in data and data['hscode']:
            if 'CTH_HSCODE' in df.columns:
                df = df[df['CTH_HSCODE'].astype(str).isin(data['hscode'])]

        if 'item' in data and data['item']:
            if 'Item_Description' in df.columns:
                df = df[df['Item_Description'].isin(data['item'])]

        filtered_count = len(df)
        preview = df.head(20).replace({np.nan: None}).to_dict(orient='records')

        print(f" Filtered from {original_count} to {filtered_count} records")

        return jsonify({
            'success': True,
            'data': preview,
            'message': f'Filter applied successfully. Found {filtered_count} records.',
            'filters_applied': data
        })
    except Exception as e:
        print(f" Filter error: {str(e)}")
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
        original_count = len(df)

        # Apply same filters as filter_data
        if 'tradeType' in data and data['tradeType']:
            if 'Type' in df.columns:
                df = df[df['Type'].isin(data['tradeType'])]

        if 'importer' in data and data['importer']:
            if 'Importer_City_State' in df.columns:
                df = df[df['Importer_City_State'].isin(data['importer'])]

        if 'supplier' in data and data['supplier']:
            if 'Country_of_Origin' in df.columns:
                df = df[df['Country_of_Origin'].isin(data['supplier'])]

        if 'years' in data and data['years']:
            # Try to filter by year from Month column first
            if 'Month' in df.columns:
                try:
                    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
                    df = df[df['Month'].dt.year.isin([int(y) for y in data['years']])]
                except:
                    # Fallback to YEAR column
                    if 'YEAR' in df.columns:
                        df = df[df['YEAR'].isin([int(y) for y in data['years']])]
            elif 'YEAR' in df.columns:
                df = df[df['YEAR'].isin([int(y) for y in data['years']])]

        if 'hscode' in data and data['hscode']:
            if 'CTH_HSCODE' in df.columns:
                df = df[df['CTH_HSCODE'].astype(str).isin(data['hscode'])]

        if 'item' in data and data['item']:
            if 'Item_Description' in df.columns:
                df = df[df['Item_Description'].isin(data['item'])]

        if len(df) == 0:
            return jsonify({
                'success': False,
                'error': 'No data found with the applied filters'
            }), 400

        # Get the value column
        value_col = data.get('value_col')
        if not value_col or value_col not in df.columns:
            return jsonify({
                'success': False,
                'error': f'Value column "{value_col}" not found in data'
            }), 400

        # Set column names for analysis based on your actual columns
        product_col = 'Item_Description'
        importer_col = 'Importer_City_State'
        supplier_col = 'Country_of_Origin'
        quantity_col = 'Quantity'

        print(f"Analysis columns: product={product_col}, importer={importer_col}, supplier={supplier_col}, value={value_col}, quantity={quantity_col}")

        # Perform analysis
        analysis_results = perform_trade_analysis(
            df.copy(),
            product_col=product_col,
            quantity_col=quantity_col,
            value_col=value_col,
            importer_col=importer_col,
            supplier_col=supplier_col
        )

        # Clean NaN values
        cleaned_results = convert_nan_to_none(analysis_results)
        json_str = json.dumps(cleaned_results, default=str)
        cleaned_results = json.loads(json_str)

        print(f" Analysis completed for {len(df)} records")

        return jsonify({
            'success': True,
            'results': cleaned_results,
            'message': f'Analyzed {len(df)} records (filtered from {original_count})'
        })
    except Exception as e:
        print(f" Analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500