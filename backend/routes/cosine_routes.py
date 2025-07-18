import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file, session, Blueprint
import os
from prophet import Prophet
from fuzzywuzzy import fuzz
from session_utils import save_df_to_session, get_df_from_session
import pandas as pd
from flask import current_app as app
from cosine_clustering import cluster_column, highlight_changes_in_excel,  get_replacement_suggestions

cosine_bp = Blueprint('cosine', __name__ , url_prefix = '/api')
@cosine_bp.route('/cosine_cluster', methods=['POST', 'OPTIONS'])
def cluster_cosine():
    if request.method == 'OPTIONS':
        # 🟢 Respond OK to preflight request
        return '', 200

    data = request.get_json()
    filename=data.get('filename')
    column = data.get('column')
    threshold = float(data.get('threshold', 0.8))

    if not column or not filename:
        return jsonify({'error': 'Column name is required'}), 400

    try:
        
        print("🔍 Checking session in cosine_cluster")
        print("🔑 Session keys:", list(session.keys()))
       # df_cleaned = get_df_from_session("cleaned_df")

       # """ if df_cleaned is None:
       #     print("❌ No df found in session under 'cleaned_df'")
       # else:
       #     print("✅ Retrieved df from session") """
        
     # """   df_cleaned = get_df_from_session("cleaned_df")

      #  if df_cleaned is None:
       #     print("❌ No df in session, trying to load from temp file")
       #     temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_cleaned.csv")
        #    if os.path.exists(temp_file_path):
         #       df_cleaned = pd.read_csv(temp_file_path)
         #       print("✅ Loaded df from temp file")
         #   else:
         #       return jsonify({'error': 'Data not found in session or temp file'}), 500"""
        cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(cleaned_file_path):
            return jsonify({'error': f'Cleaned file not found: {filename}'}), 404

        df_cleaned = pd.read_csv(cleaned_file_path)
        print("📥 Input DF shape:", df_cleaned.shape)
        print("📄 Sample values:", df_cleaned[column].dropna().head(5).tolist())


        print("📊 Column from frontend:", column)
        print("🧾 Available columns:", list(df_cleaned.columns))

        if column not in df_cleaned.columns:
            return jsonify({'error': f'Column {column} not found in data'}), 400

        df_cosine_sim = cluster_column(df_cleaned[[column]].copy(), column, threshold)

      # """  cosine_filename = f"cosine_clustered_{column.lower()}.csv"
       # cosine_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cosine_filename)
       # df_cosine_sim.to_csv(cosine_file_path, index=False) """
        cosine_filename = f"cosine_clustered_{column.lower()}.csv"
        cosine_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cosine_filename)
        df_cosine_sim.to_csv(cosine_file_path, index=False)
  # 💥 Save updated original df
        print("✅ Clustered CSV saved at:", cosine_file_path)

        highlighted_excel_path = cosine_file_path.replace('.csv', '.xlsx')
        original_df = pd.read_csv(cleaned_file_path) 
        highlight_changes_in_excel(original_df, df_cleaned, column, highlighted_excel_path)

        
        #suggestions = get_replacement_suggestions(df_cleaned[[column]].copy(), column, threshold)
        suggestions = get_replacement_suggestions(df_cleaned, column, threshold)



        return jsonify({
            'message': 'Data clustered successfully',
            'output_file': cosine_filename,
            'message': 'Suggestions generated',
            'replacement_suggestions': suggestions,
            "final_filename": os.path.basename(cosine_filename),

            'excel_file': os.path.basename(highlighted_excel_path),
            'clustered_preview': df_cosine_sim.head(10).fillna('').to_dict(orient='records')
        })

    except FileNotFoundError as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()  # 👈 add this to print actual error stack trace

        return jsonify({'error': f'Error clustering data: {str(e)}'}), 500


@cosine_bp.route('/apply_replacement', methods=['POST'])
def apply_replacement():
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
