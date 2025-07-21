from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import os
import json
from settings import Config

company_bp = Blueprint('company', __name__)

@company_bp.route('/api/load-companies', methods=['POST'])
def load_companies():
    try:
        data = request.get_json()
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        # Get unique supplier names
        if 'Supplier_Name' not in df.columns:
            return jsonify({'error': 'Supplier_Name column not found in the file'}), 400
            
        supplier_names = df['Supplier_Name'].dropna().unique().tolist()
        supplier_names = sorted([name for name in supplier_names if str(name).strip()])
        
        return jsonify({
            'success': True,
            'companies': supplier_names,
            'total_companies': len(supplier_names),
            'total_records': len(df)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error loading companies: {str(e)}'}), 500

@company_bp.route('/api/analyze-company', methods=['POST'])
def analyze_company():
    try:
        data = request.get_json()
        filename = data.get('filename')
        company_name = data.get('company_name')
        
        if not filename or not company_name:
            return jsonify({'error': 'Filename and company name are required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        # Filter data for the selected company
        company_data = df[df['Supplier_Name'] == company_name].copy()
        
        if company_data.empty:
            return jsonify({'error': f'No data found for company: {company_name}'}), 404
            
        # Perform analysis
        analysis_results = perform_company_analysis(company_data, company_name)
        
        # Convert company data to records for frontend - handle NaN values
        company_records = company_data.fillna('').to_dict('records')
        
        return jsonify({
            'success': True,
            'company_name': company_name,
            'total_records': len(company_data),
            'records': company_records[:100],  # Limit to first 100 records
            'has_more': len(company_data) > 100,
            'analysis': analysis_results
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing company: {str(e)}'}), 500

def perform_company_analysis(df, company_name):
    """Perform comprehensive analysis on company data"""
    try:
        analysis = {
            'basic_stats': {},
            'trade_patterns': {},
            'financial_insights': {},
            'geographic_analysis': {},
            'product_analysis': {},
            'trends': {}
        }
        
        # Basic Statistics
        analysis['basic_stats'] = {
            'total_transactions': len(df),
            'date_range': {
                'start': str(df['Date'].min()) if 'Date' in df.columns and not df['Date'].isna().all() else 'N/A',
                'end': str(df['Date'].max()) if 'Date' in df.columns and not df['Date'].isna().all() else 'N/A'
            },
            'unique_importers': int(df['Importer_Name'].nunique()) if 'Importer_Name' in df.columns else 0,
            'unique_products': int(df['Item_Description'].nunique()) if 'Item_Description' in df.columns else 0
        }
        
        # Trade Patterns
        if 'Trade_Type' in df.columns:
            trade_type_counts = df['Trade_Type'].value_counts().to_dict()
            analysis['trade_patterns'] = {
                'by_trade_type': trade_type_counts,
                'primary_trade_type': df['Trade_Type'].mode().iloc[0] if not df['Trade_Type'].mode().empty else 'N/A'
            }
        
        # Financial Insights
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_columns:
            financial_data = {}
            for col in numeric_columns:
                if col in ['Value', 'Quantity', 'Unit_Price', 'Amount', 'Total_Value']:
                    # Handle NaN values and convert to Python native types
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        financial_data[col] = {
                            'total': float(col_data.sum()) if not pd.isna(col_data.sum()) else 0.0,
                            'average': float(col_data.mean()) if not pd.isna(col_data.mean()) else 0.0,
                            'median': float(col_data.median()) if not pd.isna(col_data.median()) else 0.0,
                            'min': float(col_data.min()) if not pd.isna(col_data.min()) else 0.0,
                            'max': float(col_data.max()) if not pd.isna(col_data.max()) else 0.0
                        }
            analysis['financial_insights'] = financial_data
        
        # Geographic Analysis
        if 'Importer_City' in df.columns:
            top_cities = df['Importer_City'].value_counts().head(10).to_dict()
            analysis['geographic_analysis'] = {
                'top_importer_cities': top_cities,
                'total_cities': df['Importer_City'].nunique()
            }
        
        # Product Analysis
        if 'Item_Description' in df.columns:
            top_products = df['Item_Description'].value_counts().head(10).to_dict()
            analysis['product_analysis'] = {
                'top_products': top_products,
                'product_diversity': df['Item_Description'].nunique()
            }
        
        if 'HSCode' in df.columns:
            top_hscodes = df['HSCode'].value_counts().head(10).to_dict()
            analysis['product_analysis']['top_hscodes'] = top_hscodes
        
        # Time-based Trends (if date column exists)
        if 'Date' in df.columns:
            try:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df_with_valid_dates = df.dropna(subset=['Date'])
                
                if len(df_with_valid_dates) > 0:
                    df_with_valid_dates['Year'] = df_with_valid_dates['Date'].dt.year
                    df_with_valid_dates['Month'] = df_with_valid_dates['Date'].dt.month
                    
                    yearly_trends = df_with_valid_dates.groupby('Year').size().to_dict()
                    monthly_trends = df_with_valid_dates.groupby('Month').size().to_dict()
                    
                    # Convert numpy int64 to Python int
                    yearly_trends = {int(k): int(v) for k, v in yearly_trends.items()}
                    monthly_trends = {int(k): int(v) for k, v in monthly_trends.items()}
                    
                    analysis['trends'] = {
                        'yearly_distribution': yearly_trends,
                        'monthly_distribution': monthly_trends
                    }
            except Exception as e:
                analysis['trends'] = {'error': f'Date parsing error: {str(e)}'}
        
        return analysis
        
    except Exception as e:
        return {'error': f'Analysis error: {str(e)}'}

@company_bp.route('/api/export-company-data', methods=['POST'])
def export_company_data():
    try:
        data = request.get_json()
        filename = data.get('filename')
        company_name = data.get('company_name')
        
        if not filename or not company_name:
            return jsonify({'error': 'Filename and company name are required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        company_data = df[df['Supplier_Name'] == company_name].copy()
        
        if company_data.empty:
            return jsonify({'error': f'No data found for company: {company_name}'}), 404
        
        # Save filtered data to a new file
        export_filename = f"company_analysis_{company_name.replace(' ', '_')}_{filename}"
        export_path = os.path.join(Config.UPLOAD_FOLDER, export_filename)
        company_data.to_csv(export_path, index=False)
        
        return jsonify({
            'success': True,
            'export_filename': export_filename,
            'records_exported': len(company_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Export error: {str(e)}'}), 500