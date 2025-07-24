import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file, session, Blueprint
import os
from prophet import Prophet
from fuzzywuzzy import fuzz
from session_utils import save_df_to_session, get_df_from_session
import pandas as pd
from flask import current_app as app
from cosine_clustering import cluster_column, highlight_changes_in_excel,  get_replacement_suggestions

# --------------- ADDED FOR TIMEOUT HANDLING ---------------
import signal
from functools import wraps
import time

def timeout_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "timeout" in str(e).lower():
                return jsonify({"error": "Request timeout - processing taking too long"}), 408
            raise e
    return wrapper
# --------------- END TIMEOUT HANDLING ---------------

cosine_bp = Blueprint('cosine', __name__ , url_prefix = '/api')

@cosine_bp.route('/cosine_cluster', methods=['POST', 'OPTIONS'])
# --------------- ADDED TIMEOUT DECORATOR ---------------
@timeout_handler
# --------------- END TIMEOUT DECORATOR ---------------
def cluster_cosine():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,Origin")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response, 200

    data = request.get_json()
    filename = data.get('filename')
    column = data.get('column')
    threshold = float(data.get('threshold', 0.8))

    if not column or not filename:
        return jsonify({'error': 'Column name and filename are required'}), 400

    try:
        # --------------- ADDED PROGRESS LOGGING ---------------
        print("🚀 Starting cosine clustering process")
        print(f"📊 Column: {column}, Threshold: {threshold}")
        print(f"📁 Filename: {filename}")
        start_time = time.time()
        # --------------- END PROGRESS LOGGING ---------------
        
        # Define progressive clustering filename
        progressive_filename = f"progressive_clustered_{filename}"
        progressive_file_path = os.path.join(app.config['UPLOAD_FOLDER'], progressive_filename)
        
        # Check if progressive clustering file exists (for subsequent clustering steps)
        if os.path.exists(progressive_file_path):
            print("📂 Loading existing progressive clustering file")
            df_cleaned = pd.read_csv(progressive_file_path)
            print(f"✅ Loaded progressive file shape: {df_cleaned.shape}")
        else:
            # First clustering step - load original cleaned file
            print("🔄 First clustering step - loading original cleaned file")
            cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if not os.path.exists(cleaned_file_path):
                return jsonify({'error': f'Cleaned file not found: {filename}'}), 404
            
            df_cleaned = pd.read_csv(cleaned_file_path)
            print(f"✅ Loaded original file shape: {df_cleaned.shape}")

        print(f"📋 Available columns: {list(df_cleaned.columns)}")
        print(f"🔍 Sample values in {column}: {df_cleaned[column].dropna().head(5).tolist()}")

        # Validate column exists
        if column not in df_cleaned.columns:
            return jsonify({'error': f'Column {column} not found in data'}), 400

        # Perform clustering on the specified column
        print(f"⚡ Starting clustering for column: {column}")
        df_clustered = cluster_column(df_cleaned.copy(), column, threshold)
        print(f"✅ Clustering completed. Result shape: {df_clustered.shape}")

        # Save the progressively updated file (contains all clustering results so far)
        df_clustered.to_csv(progressive_file_path, index=False)
        print(f"💾 Progressive file saved: {progressive_file_path}")

        # Save column-specific file for download/preview
        cosine_filename = f"cosine_clustered_{column.lower().replace(' ', '_')}.csv"
        cosine_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cosine_filename)
        df_clustered.to_csv(cosine_file_path, index=False)
        print(f"💾 Column-specific file saved: {cosine_file_path}")

        # Create highlighted Excel file for visualization
        highlighted_excel_path = cosine_file_path.replace('.csv', '.xlsx')
        try:
            # Load original data for comparison
            original_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(original_file_path):
                original_df = pd.read_csv(original_file_path)
                highlight_changes_in_excel(original_df, df_clustered, column, highlighted_excel_path)
                print(f"📊 Excel file with highlights created: {highlighted_excel_path}")
            else:
                print("⚠️ Original file not found for highlighting")
        except Exception as e:
            print(f"⚠️ Warning: Could not create highlighted Excel file: {str(e)}")

        # Generate replacement suggestions
        print("🔍 Generating replacement suggestions...")
        try:
            suggestions = get_replacement_suggestions(df_cleaned, column, threshold)
            print(f"✅ Generated {len(suggestions)} suggestions")
        except Exception as e:
            print(f"⚠️ Warning: Could not generate suggestions: {str(e)}")
            suggestions = []

        # Prepare response data
        clustered_preview = df_clustered.head(10).fillna('').to_dict(orient='records')
        
        response_data = {
            'success': True,
            'message': 'Data clustered successfully',
            'output_file': cosine_filename,
            'progressive_file': progressive_filename,
            'final_filename': progressive_filename,  # This is what FilterPage should use
            'replacement_suggestions': suggestions,
            'clustered_preview': clustered_preview,
            'column_clustered': column,
            'threshold_used': threshold,
            'total_rows': len(df_clustered)
        }

        # Add Excel file info if it exists
        if os.path.exists(highlighted_excel_path):
            response_data['excel_file'] = os.path.basename(highlighted_excel_path)

        # --------------- ADDED COMPLETION LOGGING ---------------
        end_time = time.time()
        print(f"🎉 Clustering process completed successfully in {end_time - start_time:.2f} seconds")
        # --------------- END COMPLETION LOGGING ---------------
        
        return jsonify(response_data)

    except FileNotFoundError as e:
        error_msg = f'File not found: {str(e)}'
        print(f"❌ FileNotFoundError: {error_msg}")
        return jsonify({'error': error_msg}), 404
    
    except KeyError as e:
        error_msg = f'Missing column in data: {str(e)}'
        print(f"❌ KeyError: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    except ValueError as e:
        error_msg = f'Invalid threshold value: {str(e)}'
        print(f"❌ ValueError: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    except Exception as e:
        error_msg = f'Error clustering data: {str(e)}'
        print(f"❌ Unexpected error: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500


@cosine_bp.route('/apply_replacement', methods=['POST', 'OPTIONS'])
# --------------- ADDED TIMEOUT DECORATOR ---------------
@timeout_handler
# --------------- END TIMEOUT DECORATOR ---------------
def apply_replacement():
    if request.method == 'OPTIONS':
        # is critical for passing preflight
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response, 200
        
    data = request.get_json()
    filename = data.get('filename')
    column = data.get('column')
    target_row = int(data.get('targetRow'))
    new_value = data.get('newValue')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)

    if column not in df.columns or target_row >= len(df):
        return jsonify({'error': 'Invalid input'}), 400

    df.at[target_row, column] = new_value
    df.to_csv(filepath, index=False)

    return jsonify({'message': 'Replacement applied successfully'})