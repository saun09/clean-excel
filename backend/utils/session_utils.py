""" from flask import session
import pandas as pd
import pickle

def save_df_to_session(key,df):
    session[key] = pickle.dumps(df)

def get_df_from_session(key):
    if key in session:
        return pickle.loads(session[key])
    return None """


# session_utils.py
from flask import session
import pandas as pd

def save_df_to_session(key, df):
    session[key] = df.to_json()  # ✅ safe and compact

def get_df_from_session(key):
    print("🧪 Trying to fetch from session:", key)
    json_data = session.get(key)
    if json_data:
        print("✅ JSON data found for key:", key)
        return pd.read_json(json_data)
    print("❌ No JSON data found for key:", key)
    return None
