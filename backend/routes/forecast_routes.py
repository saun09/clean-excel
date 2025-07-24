from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
import os
from settings import Config
import json
import traceback

# Try to import Prophet, but handle if it's not available
try:
    from prophet import Prophet
    from prophet.diagnostics import performance_metrics, cross_validation
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Prophet not available - will use traditional models only")

forecast_bp = Blueprint('forecast', __name__)

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def train_prophet_model(df, forecast_column):
    """Train Prophet model and return model, historical predictions, success status, and error"""
    if not PROPHET_AVAILABLE:
        return None, None, False, "Prophet library not available"
    
    try:
        if len(df) < 2:
            return None, None, False, "Insufficient data points for Prophet model"
        
        # Check for NaN or infinite values
        if df['y'].isna().any() or np.isinf(df['y']).any():
            return None, None, False, "Data contains NaN or infinite values"
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='additive',  # Changed to additive for more stability
            changepoint_prior_scale=0.05  # Reduced for more stable trends
        )
        
        model.fit(df)
        
        # Get historical predictions
        historical = model.predict(df[['ds']])
        
        return model, historical, True, None
        
    except Exception as e:
        print(f"Prophet model error: {str(e)}")
        return None, None, False, str(e)

@forecast_bp.route('/api/load-forecast-options', methods=['POST', 'GET'])
def load_forecast_options():
    """Load available companies, forecast columns, and years from the clustered data"""
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.get_json()
            filename = data.get('filename') if data else None
        else:  # GET request
            filename = request.args.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': f'File not found: {filename}'}), 404
            
        df = pd.read_csv(filepath)
        
        # Check if required columns exist
        if 'Supplier_Name' not in df.columns:
            return jsonify({'error': 'Supplier_Name column not found in data'}), 400
        
        # Get unique companies
        companies = sorted(df['Supplier_Name'].dropna().unique().tolist())
        
        # Get numeric columns that can be forecasted
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove ID columns or other non-forecastable columns
        forecast_columns = [col for col in numeric_columns if col not in ['Unnamed: 0', 'index', 'cluster', 'level_0']]
        
        # Get available years from Month column
        years = []
        if 'Month' in df.columns:
            try:
                def extract_year(month_str):
                    try:
                        if pd.isna(month_str):
                            return None
                        month_str = str(month_str)
                        if '--' in month_str:
                            return int(month_str.split('--')[1])
                        else:
                            parsed_date = pd.to_datetime(month_str, errors='coerce')
                            return parsed_date.year if not pd.isna(parsed_date) else None
                    except:
                        return None
                
                df['temp_year'] = df['Month'].apply(extract_year)
                years = sorted([int(year) for year in df['temp_year'].dropna().unique() if year is not None])
            except Exception as e:
                print(f"Error extracting years: {e}")
                years = []
        
        return jsonify({
            'success': True,
            'companies': companies,
            'forecast_columns': forecast_columns,
            'years': years
        })
        
    except Exception as e:
        print(f"Load forecast options error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@forecast_bp.route('/api/get-products-by-company', methods=['POST','GET'])
def get_products_by_company():
    """Get available products for a specific company"""
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.get_json()
            filename = data.get('filename') if data else None
            company_name = data.get('company_name') if data else None
        else:  # GET request
            filename = request.args.get('filename')
            company_name = request.args.get('company_name')
        
        if not filename or not company_name:
            return jsonify({'error': 'Filename and company_name are required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': f'File not found: {filename}'}), 404
            
        df = pd.read_csv(filepath)
        
        # Check if required columns exist
        if 'Supplier_Name' not in df.columns or 'Item_Description' not in df.columns:
            return jsonify({'error': 'Required columns (Supplier_Name, Item_Description) not found in data'}), 400
        
        # Filter by company and get unique products
        company_df = df[df['Supplier_Name'] == company_name]
        products = sorted(company_df['Item_Description'].dropna().unique().tolist())
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        print(f"Get products by company error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500
@forecast_bp.route('/api/generate-forecast', methods=['POST','GET'])
def generate_forecast():
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided in request'}), 400
            filename = data.get('filename')
            company_name = data.get('company_name')
            product_name = data.get('product_name')
            forecast_column = data.get('forecast_column')
        else:  # GET request
            filename = request.args.get('filename')
            company_name = request.args.get('company_name')
            product_name = request.args.get('product_name')
            forecast_column = request.args.get('forecast_column')
        
        print(f"Received request - Company: {company_name}, Product: {product_name}, Column: {forecast_column}")
        
        if not all([filename, company_name, product_name, forecast_column]):
            missing = [k for k, v in {'filename': filename, 'company_name': company_name, 
                                    'product_name': product_name, 'forecast_column': forecast_column}.items() if not v]
            return jsonify({'error': f'Missing required parameters: {missing}'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': f'File not found: {filename}'}), 404
            
        df = pd.read_csv(filepath)
        print(f"Loaded dataframe with shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Check if required columns exist
        required_columns = ['Supplier_Name', 'Item_Description', 'Month', forecast_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing columns in data: {missing_columns}'}), 400
        
        # Filter data
        filtered_df = df[
            (df['Supplier_Name'] == company_name) & 
            (df['Item_Description'] == product_name)
        ].copy()
        
        print(f"Filtered dataframe shape: {filtered_df.shape}")
        
        if filtered_df.empty:
            return jsonify({'error': f'No data found for company "{company_name}" and product "{product_name}"'}), 400
        
        # Check if forecast column has valid data
        if forecast_column not in filtered_df.columns:
            return jsonify({'error': f'Forecast column "{forecast_column}" not found in data'}), 400
            
        # Remove rows with NaN values in the forecast column
        filtered_df = filtered_df.dropna(subset=[forecast_column])
        
        if filtered_df.empty:
            return jsonify({'error': f'No valid data found for forecasting in column "{forecast_column}"'}), 400
        
        # Parse the Month column correctly
        def parse_month_column(month_str):
            try:
                if pd.isna(month_str):
                    return pd.NaT
                month_str = str(month_str)
                if '--' in month_str:
                    parts = month_str.split('--')
                    if len(parts) == 2:
                        month_name = parts[0].strip()
                        year = int(parts[1].strip())
                        # Convert month name to number
                        try:
                            month_num = pd.to_datetime(month_name, format='%B').month
                        except:
                            # Try abbreviated month names
                            month_num = pd.to_datetime(month_name, format='%b').month
                        return pd.to_datetime(f"{year}-{month_num:02d}-01")
                else:
                    return pd.to_datetime(month_str, errors='coerce')
            except Exception as e:
                print(f"Error parsing month '{month_str}': {e}")
                return pd.NaT
        
        filtered_df['Month_Parsed'] = filtered_df['Month'].apply(parse_month_column)
        
        # Remove rows with invalid dates
        initial_count = len(filtered_df)
        filtered_df = filtered_df.dropna(subset=['Month_Parsed'])
        print(f"Removed {initial_count - len(filtered_df)} rows with invalid dates")
        
        if filtered_df.empty:
            return jsonify({'error': 'No valid date data found for forecasting'}), 400
            
        # Sort by date
        filtered_df = filtered_df.sort_values('Month_Parsed')
        
        # Check forecast column for numeric values
        try:
            filtered_df[forecast_column] = pd.to_numeric(filtered_df[forecast_column], errors='coerce')
            filtered_df = filtered_df.dropna(subset=[forecast_column])
        except Exception as e:
            return jsonify({'error': f'Error converting forecast column to numeric: {str(e)}'}), 400
        
        if len(filtered_df) < 2:
            return jsonify({'error': 'Insufficient data points for forecasting (minimum 2 required)'}), 400
        
        print(f"Final dataset shape: {filtered_df.shape}")
        print(f"Date range: {filtered_df['Month_Parsed'].min()} to {filtered_df['Month_Parsed'].max()}")
        
        # Get the latest year from the data and calculate next 2 years
        latest_date = filtered_df['Month_Parsed'].max()
        latest_year = latest_date.year
        forecast_years = [latest_year + 1, latest_year + 2]
        
        # Create proper time-based features
        filtered_df['month_num'] = filtered_df['Month_Parsed'].dt.month
        filtered_df['year'] = filtered_df['Month_Parsed'].dt.year
        
        # Create a proper time index based on months since start
        start_date = filtered_df['Month_Parsed'].min()
        filtered_df['months_since_start'] = ((filtered_df['Month_Parsed'] - start_date).dt.days / 30.44).round().astype(int)
        
        # Prepare training data
        X = filtered_df[['months_since_start', 'month_num']].values.astype(float)
        y = filtered_df[forecast_column].values.astype(float)
        
        print(f"Training data shape - X: {X.shape}, y: {y.shape}")
        
        # Train models
        models = {}
        predictions = {}
        metrics = {}
        
        # Linear Regression with proper scaling
        try:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            linear_model = LinearRegression()
            linear_model.fit(X_scaled, y)
            linear_pred = linear_model.predict(X_scaled)
            models['linear'] = {'model': linear_model, 'scaler': scaler}
            predictions['linear'] = linear_pred
            metrics['linear'] = {
                'mae': float(mean_absolute_error(y, linear_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y, linear_pred))),
                'r2': float(r2_score(y, linear_pred)),
                'model_type': 'Traditional'
            }
            print("Linear model trained successfully")
        except Exception as e:
            print(f"Linear model error: {e}")
            return jsonify({'error': f'Error training linear model: {str(e)}'}), 500
        
        # Polynomial Regression with scaling
        try:
            poly_features = PolynomialFeatures(degree=2)
            X_poly = poly_features.fit_transform(X_scaled)
            poly_model = LinearRegression()
            poly_model.fit(X_poly, y)
            poly_pred = poly_model.predict(X_poly)
            models['polynomial'] = {
                'model': poly_model, 
                'features': poly_features, 
                'scaler': scaler
            }
            predictions['polynomial'] = poly_pred
            metrics['polynomial'] = {
                'mae': float(mean_absolute_error(y, poly_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y, poly_pred))),
                'r2': float(r2_score(y, poly_pred)),
                'model_type': 'Traditional'
            }
            print("Polynomial model trained successfully")
        except Exception as e:
            print(f"Polynomial model error: {e}")
            # Don't fail completely, just skip polynomial
            pass
        
        # Prepare data for Prophet
        prophet_success = False
        prophet_error = None
        prophet_forecast_data = None
        
        if PROPHET_AVAILABLE:
            try:
                df_prophet = pd.DataFrame({
                    'ds': filtered_df['Month_Parsed'],
                    'y': filtered_df[forecast_column]
                })
                
                # Train Prophet model
                prophet_model, prophet_historical, prophet_success, prophet_error = train_prophet_model(df_prophet, forecast_column)
                
                if prophet_success:
                    prophet_pred = prophet_historical['yhat'].values
                    models['prophet'] = prophet_model
                    predictions['prophet'] = prophet_pred
                    
                    prophet_mae = mean_absolute_error(y, prophet_pred)
                    prophet_rmse = np.sqrt(mean_squared_error(y, prophet_pred))
                    prophet_r2 = r2_score(y, prophet_pred)
                    
                    metrics['prophet'] = {
                        'mae': float(prophet_mae),
                        'rmse': float(prophet_rmse),
                        'r2': float(prophet_r2),
                        'model_type': 'Time Series',
                        'trend_changepoints': len(prophet_model.changepoints) if hasattr(prophet_model, 'changepoints') else 0,
                        'seasonality_components': list(prophet_model.seasonalities.keys()) if hasattr(prophet_model, 'seasonalities') else []
                    }
                    print("Prophet model trained successfully")
                else:
                    print(f"Prophet model failed: {prophet_error}")
            except Exception as e:
                prophet_error = str(e)
                print(f"Prophet model exception: {e}")
        
        # Choose best model based on R² score
        if not metrics:
            return jsonify({'error': 'No models could be trained successfully'}), 500
            
        best_model_name = max(metrics.keys(), key=lambda k: metrics[k]['r2'])
        print(f"Best model: {best_model_name} with R²: {metrics[best_model_name]['r2']}")
        
        # Generate future predictions for the next 2 years (24 months)
        last_month_index = int(filtered_df['months_since_start'].max())
        future_months = []
        future_predictions = []
        
        # Generate Prophet future forecast if available
        if prophet_success:
            try:
                future_dates = pd.date_range(
                    start=latest_date + pd.DateOffset(months=1),
                    periods=24,
                    freq='MS'
                )
                
                future_df = pd.DataFrame({'ds': future_dates})
                prophet_forecast = prophet_model.predict(future_df)
                
                prophet_forecast_data = {
                    'dates': [d.strftime('%Y-%m') for d in future_dates],
                    'predictions': [max(0, float(x)) for x in prophet_forecast['yhat']],
                    'lower_bound': [max(0, float(x)) for x in prophet_forecast.get('yhat_lower', prophet_forecast['yhat'])],
                    'upper_bound': [max(0, float(x)) for x in prophet_forecast.get('yhat_upper', prophet_forecast['yhat'])],
                    'trend': [float(x) for x in prophet_forecast.get('trend', prophet_forecast['yhat'])],
                    'seasonal': [float(x) for x in prophet_forecast.get('yearly', [0]*24)]
                }
            except Exception as e:
                print(f"Error generating Prophet forecast: {e}")
                prophet_forecast_data = None
        
        # Generate 24 months forecast for all models
        for year_offset in range(2):  # Next 2 years
            forecast_year = latest_year + 1 + year_offset
            for month in range(1, 13):  # 12 months per year
                # Calculate months since start for future prediction
                future_month_index = last_month_index + (year_offset * 12) + month
                month_date = datetime(forecast_year, month, 1)
                
                try:
                    if best_model_name == 'linear' and 'linear' in models:
                        # Use scaled features for prediction
                        X_future = scaler.transform([[future_month_index, month]])
                        pred = models['linear']['model'].predict(X_future)[0]
                    elif best_model_name == 'polynomial' and 'polynomial' in models:
                        # Use scaled and polynomial features for prediction
                        X_future_scaled = models['polynomial']['scaler'].transform([[future_month_index, month]])
                        X_future_poly = models['polynomial']['features'].transform(X_future_scaled)
                        pred = models['polynomial']['model'].predict(X_future_poly)[0]
                    elif best_model_name == 'prophet' and prophet_success and prophet_forecast_data:
                        # Use Prophet prediction
                        month_idx = (year_offset * 12) + (month - 1)
                        if month_idx < len(prophet_forecast_data['predictions']):
                            pred = prophet_forecast_data['predictions'][month_idx]
                        else:
                            pred = prophet_forecast_data['predictions'][-1] if prophet_forecast_data['predictions'] else 0
                    else:
                        # Fallback to linear if available
                        if 'linear' in models:
                            X_future = scaler.transform([[future_month_index, month]])
                            pred = models['linear']['model'].predict(X_future)[0]
                        else:
                            pred = np.mean(y)  # Ultimate fallback
                    
                    future_months.append(month_date.strftime('%Y-%m'))
                    future_predictions.append(float(max(0, pred)))
                    
                except Exception as e:
                    print(f"Error generating prediction for {month_date}: {e}")
                    # Use average as fallback
                    future_months.append(month_date.strftime('%Y-%m'))
                    future_predictions.append(float(np.mean(y)))
        
        # Calculate trends and insights
        historical_values = y.astype(float)
        recent_trend = 'increasing' if len(historical_values) > 1 and historical_values[-1] > historical_values[0] else 'decreasing'
        volatility = float(np.std(historical_values) / np.mean(historical_values)) if np.mean(historical_values) > 0 else 0.0
        
        # Seasonal analysis
        try:
            monthly_avg = filtered_df.groupby('month_num')[forecast_column].mean().to_dict()
            monthly_avg = {int(k): float(v) for k, v in monthly_avg.items()}
            
            peak_months = sorted(monthly_avg.items(), key=lambda x: x[1], reverse=True)[:3]
            low_months = sorted(monthly_avg.items(), key=lambda x: x[1])[:3]
        except Exception as e:
            print(f"Error in seasonal analysis: {e}")
            peak_months = []
            low_months = []
        
        # Calculate year-wise forecast totals
        year_forecasts = {}
        for i, year in enumerate(forecast_years):
            year_start_idx = i * 12
            year_end_idx = (i + 1) * 12
            year_predictions = future_predictions[year_start_idx:year_end_idx]
            year_total = sum(year_predictions)
            year_avg = year_total / len(year_predictions) if year_predictions else 0
            year_forecasts[str(year)] = {
                'total': round(float(year_total), 2),
                'average': round(float(year_avg), 2)
            }
        
        # Prepare response data
        historical_data = {
            'dates': [x.strftime('%Y-%m') for x in filtered_df['Month_Parsed']],
            'actual_values': [float(x) for x in y],
            'linear_predictions': [float(x) for x in predictions.get('linear', [])],
            'polynomial_predictions': [float(x) for x in predictions.get('polynomial', [])]
        }
        
        if prophet_success and 'prophet' in predictions:
            historical_data['prophet_predictions'] = [float(x) for x in predictions['prophet']]
        
        forecast_data = {
            'dates': future_months,
            'predictions': future_predictions,
            'best_model': best_model_name,
            'forecast_years': forecast_years,
            'prophet_forecast': prophet_forecast_data if prophet_success else None
        }
        
        # Enhanced trend analysis
        prophet_insights = {}
        if prophet_success and prophet_forecast_data:
            try:
                prophet_insights = {
                    'trend_direction': 'increasing' if prophet_forecast_data['trend'][-1] > prophet_forecast_data['trend'][0] else 'decreasing',
                    'seasonality_strength': float(np.std(prophet_forecast_data['seasonal'])) if prophet_forecast_data['seasonal'] else 0.0,
                    'uncertainty_range': {
                        'avg_lower': float(np.mean(prophet_forecast_data['lower_bound'])),
                        'avg_upper': float(np.mean(prophet_forecast_data['upper_bound'])),
                        'avg_width': float(np.mean([u - l for u, l in zip(prophet_forecast_data['upper_bound'], prophet_forecast_data['lower_bound'])]))
                    }
                }
            except Exception as e:
                print(f"Error calculating prophet insights: {e}")
                prophet_insights = {}
        
        trend_analysis = {
            'historical_trend': recent_trend,
            'volatility': round(volatility * 100, 2),
            'average_value': round(float(np.mean(historical_values)), 2),
            'total_data_points': len(historical_values),
            'latest_year': latest_year,
            'peak_months': [
                {
                    'month': int(month), 
                    'value': round(float(value), 2), 
                    'month_name': datetime(2024, month, 1).strftime('%B')
                } for month, value in peak_months
            ],
            'low_months': [
                {
                    'month': int(month), 
                    'value': round(float(value), 2), 
                    'month_name': datetime(2024, month, 1).strftime('%B')
                } for month, value in low_months
            ],
            'forecast_total_24_months': round(float(sum(future_predictions)), 2),
            'forecast_average_monthly': round(float(np.mean(future_predictions)), 2),
            'year_wise_forecasts': year_forecasts,
            'prophet_insights': prophet_insights
        }
        
        response_data = {
            'success': True,
            'historical_data': historical_data,
            'forecast_data': forecast_data,
            'model_metrics': metrics,
            'trend_analysis': trend_analysis,
            'company_name': str(company_name),
            'product_name': str(product_name),
            'forecast_column': str(forecast_column),
            'forecast_years': forecast_years,
            'prophet_available': prophet_success,
            'prophet_error': prophet_error if not prophet_success else None
        }
        
        return jsonify(convert_numpy_types(response_data))
        
    except Exception as e:
        print(f"Forecast error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500