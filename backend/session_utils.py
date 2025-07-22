from flask import session
import pandas as pd

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_df_to_session(df, key='df'):
    """
    Save a DataFrame to session storage using a key.
    By default, saves under 'df' key (can be 'df_cleaned', 'df_clustered' etc.)
    """
    try:
        session[key] = df.to_json(orient='split')
        session.modified = True
        print(f"Saved DataFrame to session under key '{key}'")
    except Exception as e:
        print(f" Failed to save DataFrame to session: {str(e)}")


def get_df_from_session(key='df'):
    """
    Retrieve a DataFrame from session using key.
    By default, fetches from key 'df' (can be 'df_cleaned', 'df_clustered' etc.)
    """
    if key not in session:
        print(f" No DataFrame in session under key '{key}'")
        return None
    try:
        df = pd.read_json(session[key], orient='split')
        print(f" Loaded DataFrame from session key '{key}'")
        return df
    except Exception as e:
        print(f" Error loading DataFrame from session: {str(e)}")
        return None
