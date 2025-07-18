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

        # Populate trade types
        if 'Trade_Type' in df.columns:
            options['trade_types'] = sorted(df['Trade_Type'].dropna().unique().tolist())

        # Populate importer cities (handle clustered column names)
        importer_cols = ['Importer_City_State', 'Importer_City_State_cluster', 'Importer_Name', 'Importer_Name_cluster']
        for col in importer_cols:
            if col in df.columns:
                options['importer_cities'] = sorted(df[col].dropna().unique().tolist())
                break

        # Populate supplier countries (handle clustered column names)
        supplier_cols = ['Country_of_Origin', 'Country_of_Origin_cluster', 'Supplier_Name', 'Supplier_Name_cluster']
        for col in supplier_cols:
            if col in df.columns:
                options['supplier_countries'] = sorted(df[col].dropna().unique().tolist())
                break

        # Populate numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove index-like columns
        numeric_cols = [col for col in numeric_cols if not col.lower().startswith('unnamed')]
        options['numeric_columns'] = numeric_cols

        # Populate years
        date_cols = ['Date', 'Date_of_Arrival', 'Year']
        for col in date_cols:
            if col in df.columns:
                if col == 'Year':
                    options['years'] = sorted(df[col].dropna().unique().tolist())
                else:
                    # Try to extract year from date columns
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        years = df[col].dt.year.dropna().unique().tolist()
                        options['years'] = sorted(years)
                    except:
                        pass
                break

        # Populate HS codes
        hscode_cols = ['HS_Code', 'HSCode', 'HS_CODE']
        for col in hscode_cols:
            if col in df.columns:
                options['hscodes'] = sorted(df[col].dropna().astype(str).unique().tolist())
                break

        # Populate item descriptions (handle clustered column names)
        item_cols = ['Item_Description', 'Item_Description_cluster', 'Product_Description', 'Product_Description_cluster']
        for col in item_cols:
            if col in df.columns:
                options['item_descriptions'] = sorted(df[col].dropna().unique().tolist())
                break

        print(f"✅ Filter options loaded for {len(df)} records")
        print(f"Available columns: {df.columns.tolist()}")
        print(f"Options: {options}")

        return jsonify({
            'success': True,
            'options': options,
            'message': 'Filter options loaded successfully'
        })
    except Exception as e:
        print(f"❌ Error loading filter options: {str(e)}")
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
            if 'Trade_Type' in df.columns:
                df = df[df['Trade_Type'].isin(data['tradeType'])]

        if 'importer' in data and data['importer']:
            importer_cols = ['Importer_City_State', 'Importer_City_State_cluster', 'Importer_Name', 'Importer_Name_cluster']
            for col in importer_cols:
                if col in df.columns:
                    df = df[df[col].isin(data['importer'])]
                    break

        if 'supplier' in data and data['supplier']:
            supplier_cols = ['Country_of_Origin', 'Country_of_Origin_cluster', 'Supplier_Name', 'Supplier_Name_cluster']
            for col in supplier_cols:
                if col in df.columns:
                    df = df[df[col].isin(data['supplier'])]
                    break

        if 'years' in data and data['years']:
            date_cols = ['Date', 'Date_of_Arrival', 'Year']
            for col in date_cols:
                if col in df.columns:
                    if col == 'Year':
                        df = df[df[col].isin(data['years'])]
                    else:
                        # Try to filter by year from date columns
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            df = df[df[col].dt.year.isin([int(y) for y in data['years']])]
                        except:
                            pass
                    break

        if 'hscode' in data and data['hscode']:
            hscode_cols = ['HS_Code', 'HSCode', 'HS_CODE']
            for col in hscode_cols:
                if col in df.columns:
                    df = df[df[col].astype(str).isin(data['hscode'])]
                    break

        if 'item' in data and data['item']:
            item_cols = ['Item_Description', 'Item_Description_cluster', 'Product_Description', 'Product_Description_cluster']
            for col in item_cols:
                if col in df.columns:
                    df = df[df[col].isin(data['item'])]
                    break

        filtered_count = len(df)
        preview = df.head(20).replace({np.nan: None}).to_dict(orient='records')

        print(f"✅ Filtered from {original_count} to {filtered_count} records")

        return jsonify({
            'success': True,
            'data': preview,
            'message': f'Filter applied successfully. Found {filtered_count} records.',
            'filters_applied': data
        })
    except Exception as e:
        print(f"❌ Filter error: {str(e)}")
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
            if 'Trade_Type' in df.columns:
                df = df[df['Trade_Type'].isin(data['tradeType'])]

        if 'importer' in data and data['importer']:
            importer_cols = ['Importer_City_State', 'Importer_City_State_cluster', 'Importer_Name', 'Importer_Name_cluster']
            for col in importer_cols:
                if col in df.columns:
                    df = df[df[col].isin(data['importer'])]
                    break

        if 'supplier' in data and data['supplier']:
            supplier_cols = ['Country_of_Origin', 'Country_of_Origin_cluster', 'Supplier_Name', 'Supplier_Name_cluster']
            for col in supplier_cols:
                if col in df.columns:
                    df = df[df[col].isin(data['supplier'])]
                    break

        if 'years' in data and data['years']:
            date_cols = ['Date', 'Date_of_Arrival', 'Year']
            for col in date_cols:
                if col in df.columns:
                    if col == 'Year':
                        df = df[df[col].isin(data['years'])]
                    else:
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            df = df[df[col].dt.year.isin([int(y) for y in data['years']])]
                        except:
                            pass
                    break

        if 'hscode' in data and data['hscode']:
            hscode_cols = ['HS_Code', 'HSCode', 'HS_CODE']
            for col in hscode_cols:
                if col in df.columns:
                    df = df[df[col].astype(str).isin(data['hscode'])]
                    break

        if 'item' in data and data['item']:
            item_cols = ['Item_Description', 'Item_Description_cluster', 'Product_Description', 'Product_Description_cluster']
            for col in item_cols:
                if col in df.columns:
                    df = df[df[col].isin(data['item'])]
                    break

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

        # Determine correct column names for analysis
        product_col = None
        for col in ['Item_Description_cluster', 'Item_Description', 'Product_Description_cluster', 'Product_Description']:
            if col in df.columns:
                product_col = col
                break

        importer_col = None
        for col in ['Importer_City_State_cluster', 'Importer_City_State', 'Importer_Name_cluster', 'Importer_Name']:
            if col in df.columns:
                importer_col = col
                break

        supplier_col = None
        for col in ['Country_of_Origin_cluster', 'Country_of_Origin', 'Supplier_Name_cluster', 'Supplier_Name']:
            if col in df.columns:
                supplier_col = col
                break

        quantity_col = None
        for col in ['Quantity', 'Qty', 'Quantity_cluster']:
            if col in df.columns:
                quantity_col = col
                break

        print(f"✅ Analysis columns: product={product_col}, importer={importer_col}, supplier={supplier_col}, value={value_col}, quantity={quantity_col}")

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

        print(f"✅ Analysis completed for {len(df)} records")

        return jsonify({
            'success': True,
            'results': cleaned_results,
            'message': f'Analyzed {len(df)} records (filtered from {original_count})'
        })
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500