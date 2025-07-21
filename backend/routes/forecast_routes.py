from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from prophet import Prophet
from prophet.diagnostics import performance_metrics, cross_validation
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
import os
from settings import Config
import json

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
    try:
        if len(df) < 2:
            return None, None, False, "Insufficient data points for Prophet model"
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        
        model.fit(df)
        
        # Get historical predictions
        historical = model.predict(df[['ds']])
        
        return model, historical, True, None
        
    except Exception as e:
        print(f"Prophet model error: {str(e)}")
        return None, None, False, str(e)

@forecast_bp.route('/api/load-forecast-options', methods=['POST'])
def load_forecast_options():
    """Load available companies, forecast columns, and years from the clustered data"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        # Get unique companies (assuming Supplier_Name column exists)
        companies = sorted(df['Supplier_Name'].dropna().unique().tolist())
        
        # Get numeric columns that can be forecasted (exclude non-numeric columns)
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove ID columns or other non-forecastable columns
        forecast_columns = [col for col in numeric_columns if col not in ['Unnamed: 0', 'index', 'cluster']]
        
        # Get available years from Month column
        years = []
        if 'Month' in df.columns:
            try:
                # Parse month column to extract years
                def extract_year(month_str):
                    try:
                        if '--' in str(month_str):
                            return int(str(month_str).split('--')[1])
                        else:
                            return pd.to_datetime(month_str, errors='coerce').year
                    except:
                        return None
                
                df['temp_year'] = df['Month'].apply(extract_year)
                years = sorted([year for year in df['temp_year'].dropna().unique() if year is not None])
                years = [int(year) for year in years]
            except:
                years = []
        
        return jsonify({
            'success': True,
            'companies': companies,
            'forecast_columns': forecast_columns,
            'years': years
        })
        
    except Exception as e:
        print(f"Load forecast options error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/api/get-products-by-company', methods=['POST'])
def get_products_by_company():
    """Get available products for a specific company"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        company_name = data.get('company_name')
        
        if not filename or not company_name:
            return jsonify({'error': 'Filename and company_name are required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        # Filter by company and get unique products
        company_df = df[df['Supplier_Name'] == company_name]
        products = sorted(company_df['Item_Description'].dropna().unique().tolist())
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        print(f"Get products by company error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/api/generate-forecast', methods=['POST'])
def generate_forecast():
    try:
        data = request.get_json()
        filename = data.get('filename')
        company_name = data.get('company_name')
        product_name = data.get('product_name')
        forecast_column = data.get('forecast_column')
        
        if not all([filename, company_name, product_name, forecast_column]):
            return jsonify({'error': 'All parameters are required'}), 400
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
            
        df = pd.read_csv(filepath)
        
        # Filter data - Use correct column names based on your data
        filtered_df = df[
            (df['Supplier_Name'] == company_name) & 
            (df['Item_Description'] == product_name)
        ].copy()
        
        if filtered_df.empty:
            return jsonify({'error': 'No data found for selected filters'}), 400
        
        # Parse the Month column correctly - it seems to be in "Month--Year" format
        def parse_month_column(month_str):
            try:
                if '--' in str(month_str):
                    month_year = str(month_str).split('--')
                    month_name = month_year[0]
                    year = month_year[1]
                    # Convert month name to number
                    month_num = pd.to_datetime(month_name, format='%B').month
                    return pd.to_datetime(f"{year}-{month_num:02d}-01")
                else:
                    return pd.to_datetime(month_str, errors='coerce')
            except:
                return pd.NaT
        
        filtered_df['Month_Parsed'] = filtered_df['Month'].apply(parse_month_column)
        filtered_df = filtered_df.dropna(subset=['Month_Parsed', forecast_column])
        filtered_df = filtered_df.sort_values('Month_Parsed')
        
        if len(filtered_df) < 2:
            return jsonify({'error': 'Insufficient data points for forecasting (minimum 2 required)'}), 400
        
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
        
        # Train models
        models = {}
        predictions = {}
        metrics = {}
        
        # Linear Regression with proper scaling
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
        
        # Polynomial Regression with scaling
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
        
        # Prepare data for Prophet
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
                'trend_changepoints': len(prophet_model.changepoints),
                'seasonality_components': list(prophet_model.seasonalities.keys())
            }
        
        # Choose best model based on R² score
        best_model_name = max(metrics.keys(), key=lambda k: metrics[k]['r2'])
        
        # Generate future predictions for the next 2 years (24 months)
        last_month_index = int(filtered_df['months_since_start'].max())
        future_months = []
        future_predictions = []
        prophet_forecast_data = None
        
        # Generate Prophet future forecast
        if prophet_success:
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
                'lower_bound': [max(0, float(x)) for x in prophet_forecast['yhat_lower']],
                'upper_bound': [max(0, float(x)) for x in prophet_forecast['yhat_upper']],
                'trend': [float(x) for x in prophet_forecast['trend']],
                'seasonal': [float(x) for x in prophet_forecast.get('yearly', [0]*24)]
            }
        
        # Generate 24 months forecast for all models
        for year_offset in range(2):  # Next 2 years
            forecast_year = latest_year + 1 + year_offset
            for month in range(1, 13):  # 12 months per year
                # Calculate months since start for future prediction
                future_month_index = last_month_index + (year_offset * 12) + month
                month_date = datetime(forecast_year, month, 1)
                
                if best_model_name == 'linear':
                    # Use scaled features for prediction
                    X_future = scaler.transform([[future_month_index, month]])
                    pred = models['linear']['model'].predict(X_future)[0]
                elif best_model_name == 'polynomial':
                    # Use scaled and polynomial features for prediction
                    X_future_scaled = scaler.transform([[future_month_index, month]])
                    X_future_poly = models['polynomial']['features'].transform(X_future_scaled)
                    pred = models['polynomial']['model'].predict(X_future_poly)[0]
                elif best_model_name == 'prophet' and prophet_success:
                    # Use Prophet prediction
                    month_idx = (year_offset * 12) + (month - 1)
                    if month_idx < len(prophet_forecast_data['predictions']):
                        pred = prophet_forecast_data['predictions'][month_idx]
                    else:
                        pred = prophet_forecast_data['predictions'][-1]
                else:
                    # Fallback to linear
                    X_future = scaler.transform([[future_month_index, month]])
                    pred = models['linear']['model'].predict(X_future)[0]
                
                future_months.append(month_date.strftime('%Y-%m'))
                future_predictions.append(float(max(0, pred)))
        
        # Calculate trends and insights
        historical_values = y.astype(float)
        recent_trend = 'increasing' if len(historical_values) > 1 and historical_values[-1] > historical_values[0] else 'decreasing'
        volatility = float(np.std(historical_values) / np.mean(historical_values)) if np.mean(historical_values) > 0 else 0.0
        
        # Seasonal analysis
        monthly_avg = filtered_df.groupby('month_num')[forecast_column].mean().to_dict()
        monthly_avg = {int(k): float(v) for k, v in monthly_avg.items()}
        
        peak_months = sorted(monthly_avg.items(), key=lambda x: x[1], reverse=True)[:3]
        low_months = sorted(monthly_avg.items(), key=lambda x: x[1])[:3]
        
        # Calculate year-wise forecast totals
        year_forecasts = {}
        for i, year in enumerate(forecast_years):
            year_start_idx = i * 12
            year_end_idx = (i + 1) * 12
            year_total = sum(future_predictions[year_start_idx:year_end_idx])
            year_avg = year_total / 12
            year_forecasts[str(year)] = {
                'total': round(float(year_total), 2),
                'average': round(float(year_avg), 2)
            }
        
        # Prepare response data
        historical_data = {
            'dates': [x.strftime('%Y-%m') for x in filtered_df['Month_Parsed']],
            'actual_values': [float(x) for x in y],
            'linear_predictions': [float(x) for x in predictions['linear']],
            'polynomial_predictions': [float(x) for x in predictions['polynomial']]
        }
        
        if prophet_success:
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
            prophet_insights = {
                'trend_direction': 'increasing' if prophet_forecast_data['trend'][-1] > prophet_forecast_data['trend'][0] else 'decreasing',
                'seasonality_strength': float(np.std(prophet_forecast_data['seasonal'])) if prophet_forecast_data['seasonal'] else 0.0,
                'uncertainty_range': {
                    'avg_lower': float(np.mean(prophet_forecast_data['lower_bound'])),
                    'avg_upper': float(np.mean(prophet_forecast_data['upper_bound'])),
                    'avg_width': float(np.mean([u - l for u, l in zip(prophet_forecast_data['upper_bound'], prophet_forecast_data['lower_bound'])]))
                }
            }
        
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
        print(f"Forecast error: {str(e)}")  # Add logging
        return jsonify({'error': str(e)}), 500