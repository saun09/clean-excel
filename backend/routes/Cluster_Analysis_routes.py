from flask import Blueprint, request, jsonify, session
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import os
from settings import Config
import json
from datetime import datetime

cluster_analysis_bp = Blueprint('cluster', __name__)

@cluster_analysis_bp.route('/api/get-column-headers', methods=['GET'])
def get_column_headers():
    """Get available column headers from uploaded files"""
    try:
        upload_folder = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            return jsonify({'error': 'Upload folder not found'}), 404
        
        files = [f for f in os.listdir(upload_folder) if f.endswith('.csv')]
        if not files:
            return jsonify({'error': 'No CSV files found'}), 404
        
        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(upload_folder, f)))
        filepath = os.path.join(upload_folder, latest_file)
        
        df = pd.read_csv(filepath)
        columns = df.columns.tolist()
        
        # Get basic data info
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        return jsonify({
            'success': True,
            'columns': columns,
            'numeric_columns': numeric_columns,
            'filename': latest_file,
            'rows': len(df)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cluster_analysis_bp.route('/api/perform-cluster-analysis', methods=['POST'])
def perform_cluster_analysis():
    """Perform simple cluster analysis with business-friendly metrics"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        selected_columns = data.get('columns', [])
        n_clusters = data.get('n_clusters', 5)
        
        if not filename or not selected_columns:
            return jsonify({'error': 'Filename and columns are required'}), 400
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        df = pd.read_csv(filepath)
        
        # Validate columns
        missing_cols = [col for col in selected_columns if col not in df.columns]
        if missing_cols:
            return jsonify({'error': f'Columns not found: {missing_cols}'}), 400
        
        # Simple preprocessing for clustering
        cluster_data = df[selected_columns].copy()
        cluster_data = cluster_data.fillna('Unknown')
        
        # Convert all data to numeric for simple clustering
        processed_data = []
        for col in selected_columns:
            if cluster_data[col].dtype == 'object':
                le = LabelEncoder()
                encoded = le.fit_transform(cluster_data[col].astype(str))
                processed_data.append(encoded.reshape(-1, 1))
            else:
                processed_data.append(cluster_data[col].values.reshape(-1, 1))
        
        X = np.hstack(processed_data)
        
        # Simple K-means clustering
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Add clusters to original data
        df_with_clusters = df.copy()
        df_with_clusters['Cluster'] = cluster_labels
        
        # Generate simple business metrics
        cluster_summary = []
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for cluster_id in range(n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_subset = df[cluster_mask]
            
            summary = {
                'cluster_id': cluster_id,
                'size': int(np.sum(cluster_mask)),
                'percentage': round((np.sum(cluster_mask) / len(df)) * 100, 1)
            }
            
            # Basic statistics for selected columns
            characteristics = {}
            for col in selected_columns:
                if col in numeric_columns:
                    col_data = cluster_subset[col].dropna()
                    if len(col_data) > 0:
                        characteristics[col] = {
                            'type': 'numeric',
                            'count': len(col_data),
                            'total': round(col_data.sum(), 2),
                            'average': round(col_data.mean(), 2),
                            'min': round(col_data.min(), 2),
                            'max': round(col_data.max(), 2)
                        }
                else:
                    top_values = cluster_subset[col].value_counts().head(3)
                    characteristics[col] = {
                        'type': 'text',
                        'count': len(cluster_subset[col].dropna()),
                        'top_values': [
                            {'value': str(val), 'count': int(count)} 
                            for val, count in top_values.items()
                        ]
                    }
            
            summary['characteristics'] = characteristics
            cluster_summary.append(summary)
        
        # Overall statistics
        overall_stats = {}
        for col in selected_columns:
            if col in numeric_columns:
                col_data = df[col].dropna()
                overall_stats[col] = {
                    'type': 'numeric',
                    'total': round(col_data.sum(), 2),
                    'average': round(col_data.mean(), 2),
                    'count': len(col_data)
                }
        
        # Time-based trend analysis if Month column exists
        trend_analysis = None
        if 'Month' in df.columns:
            try:
                # Convert Month to datetime if possible
                df['Month_Date'] = pd.to_datetime(df['Month'], errors='coerce')
                monthly_trends = []
                
                for cluster_id in range(n_clusters):
                    cluster_data = df[df_with_clusters['Cluster'] == cluster_id]
                    if 'Month_Date' in cluster_data.columns:
                        monthly_counts = cluster_data.groupby(cluster_data['Month_Date'].dt.to_period('M')).size()
                        trend_data = [
                            {'month': str(month), 'count': int(count), 'cluster': cluster_id}
                            for month, count in monthly_counts.items()
                        ]
                        monthly_trends.extend(trend_data)
                
                trend_analysis = monthly_trends
            except:
                pass
        
        # Save clustered data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clustered_filename = f"clustered_data_{timestamp}.csv"
        clustered_filepath = os.path.join(Config.UPLOAD_FOLDER, clustered_filename)
        df_with_clusters.to_csv(clustered_filepath, index=False)
        
        return jsonify({
            'success': True,
            'clustered_filename': clustered_filename,
            'n_clusters': n_clusters,
            'total_records': len(df),
            'cluster_summary': cluster_summary,
            'overall_statistics': overall_stats,
            'trend_analysis': trend_analysis,
            'features_used': selected_columns
        })
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@cluster_analysis_bp.route('/api/get-cluster-comparison', methods=['POST'])
def get_cluster_comparison():
    """Compare clusters with simple metrics"""
    try:
        data = request.get_json()
        filename = data.get('clustered_filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        df = pd.read_csv(filepath)
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'Cluster' in numeric_columns:
            numeric_columns.remove('Cluster')
        
        comparison_data = []
        clusters = df['Cluster'].unique()
        
        for col in numeric_columns:
            col_comparison = {'column': col, 'clusters': []}
            for cluster in sorted(clusters):
                cluster_data = df[df['Cluster'] == cluster][col].dropna()
                col_comparison['clusters'].append({
                    'cluster_id': int(cluster),
                    'total': round(cluster_data.sum(), 2),
                    'average': round(cluster_data.mean(), 2),
                    'count': len(cluster_data)
                })
            comparison_data.append(col_comparison)
        
        return jsonify({
            'success': True,
            'comparison_data': comparison_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500