import os
import pandas as pd
print("✅ files_utils loaded")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx'}

def generate_preview_data(file_path):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            return []
        return df.head(10).fillna('').to_dict(orient='records')
    except Exception as e:
        print(f"⚠️ Error generating preview: {str(e)}")
        return []