import numpy as np

def convert_nan_to_none(obj):
    if isinstance(obj, dict):
        return {k: convert_nan_to_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_nan_to_none(item) for item in obj]
    elif isinstance(obj, float) and (np.isnan(obj) or obj != obj):
        return None
    elif isinstance(obj, np.floating) and np.isnan(obj):
        return None
    elif obj is np.nan:
        return None
    else:
        return obj
