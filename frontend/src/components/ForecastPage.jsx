import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import './css/ForecastAnalysis.css';
import { useNavigate } from 'react-router-dom';

const ForecastPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);
  
  // Form states
  const [companies, setCompanies] = useState([]);
  const [products, setProducts] = useState([]);
  const [forecastColumns, setForecastColumns] = useState([]);
  const [years, setYears] = useState([]);
  
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedColumn, setSelectedColumn] = useState('');
  const navigate = useNavigate();
  
  // Results state
  const [forecastResults, setForecastResults] = useState(null);
  
  const clusteredFilename = sessionStorage.getItem("finalClusteredFilename");

  useEffect(() => {
    if (clusteredFilename) {
      loadForecastOptions();
    } else {
      setError('No clustered file found. Please run clustering analysis first.');
    }
  }, [clusteredFilename]);

  const loadForecastOptions = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/load-forecast-options`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ filename: clusteredFilename })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Load forecast options error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setCompanies(data.companies || []);
        setForecastColumns(data.forecast_columns || []);
        setYears(data.years || []);
      } else {
        setError(data.error || 'Failed to load forecast options');
      }
    } catch (err) {
      console.error('Load forecast options error:', err);
      setError('Error loading forecast options: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadProductsByCompany = async (companyName) => {
    if (!companyName) {
      setProducts([]);
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/get-products-by-company`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          filename: clusteredFilename,
          company_name: companyName 
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Load products error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setProducts(data.products || []);
      } else {
        setError(data.error || 'Failed to load products');
      }
    } catch (err) {
      console.error('Load products error:', err);
      setError('Error loading products: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyChange = (e) => {
    const company = e.target.value;
    setSelectedCompany(company);
    setSelectedProduct('');
    setProducts([]);
    if (company) {
      loadProductsByCompany(company);
    }
  };

  const generateForecast = async () => {
    if (!selectedCompany || !selectedProduct || !selectedColumn) {
      setError('Please fill in all required fields');
      return;
    }
    
    if (!clusteredFilename) {
      setError('No clustered file found. Please run clustering analysis first.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const requestData = {
        filename: clusteredFilename,
        company_name: selectedCompany,
        product_name: selectedProduct,
        forecast_column: selectedColumn
      };

      console.log("Sending forecast request with:", requestData);

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/generate-forecast`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorText = await response.text();
          console.error("Error response body:", errorText);
          
          // Try to parse as JSON to get more detailed error
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.error || errorData.message || errorText;
          } catch {
            errorMessage = errorText || errorMessage;
          }
        } catch (textError) {
          console.error("Could not read error response:", textError);
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      console.log("Forecast response data:", data);
      
      if (data.success) {
        setForecastResults(data);
        setStep(2);
      } else {
        setError(data.error || 'Failed to generate forecast');
      }
    } catch (err) {
      console.error('Generate forecast error:', err);
      setError('Error generating forecast: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!forecastResults) return { historicalData: [], forecastData: [], combinedData: [] };
    
    const { historical_data, forecast_data } = forecastResults;
    
    const historicalData = historical_data.dates.map((date, index) => ({
      date,
      actual: historical_data.actual_values[index],
      linear: historical_data.linear_predictions[index],
      polynomial: historical_data.polynomial_predictions[index],
      ...(historical_data.prophet_predictions && { prophet: historical_data.prophet_predictions[index] })
    }));
    
    const forecastData = forecast_data.dates.map((date, index) => ({
      date,
      forecast: forecast_data.predictions[index]
    }));
    
    const combinedData = [
      ...historicalData.map(item => ({ ...item, type: 'historical' })),
      ...forecastData.map(item => ({ ...item, type: 'forecast' }))
    ];
    
    return { historicalData, forecastData, combinedData };
  };

  const prepareSeasonalData = () => {
    if (!forecastResults?.trend_analysis) return [];
    
    return forecastResults.trend_analysis.peak_months.map(item => ({
      month: item.month_name,
      value: item.value,
      type: 'peak'
    })).concat(
      forecastResults.trend_analysis.low_months.map(item => ({
        month: item.month_name,
        value: item.value,
        type: 'low'
      }))
    );
  };

  const prepareYearlyForecastData = () => {
    if (!forecastResults?.trend_analysis?.year_wise_forecasts) return [];
    
    return Object.entries(forecastResults.trend_analysis.year_wise_forecasts).map(([year, data]) => ({
      year,
      total: data.total,
      average: data.average
    }));
  };

  const { historicalData, forecastData, combinedData } = prepareChartData();
  const seasonalData = prepareSeasonalData();
  const yearlyForecastData = prepareYearlyForecastData();

  if (loading) {
    return (
      <div className="forecast-page">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading forecast data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="forecast-page">
      <div className="page-header">
        <h1>Forecast Analysis</h1>
        <p>Generate detailed forecasts and trend analysis for the next 2 years</p>
      </div>

      {error && (
        <div className="error-message">
          <i className="error-icon">⚠️</i>
          {error}
        </div>
      )}

      {step === 1 && (
        <div className="forecast-form">
          <div className="form-section">
            <h2>Select Forecast Parameters</h2>
            <p className="form-note">The system will automatically forecast for the next 2 years based on your data.</p>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="company">Company Name:</label>
                <select
                  id="company"
                  value={selectedCompany}
                  onChange={handleCompanyChange}
                  disabled={loading}
                >
                  <option value="">Select Company...</option>
                  {companies.map(company => (
                    <option key={company} value={company}>{company}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="product">Product:</label>
                <select
                  id="product"
                  value={selectedProduct}
                  onChange={(e) => setSelectedProduct(e.target.value)}
                  disabled={loading || !selectedCompany}
                >
                  <option value="">Select Product...</option>
                  {products.map(product => (
                    <option key={product} value={product}>{product}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="column">Column to Forecast:</label>
                <select
                  id="column"
                  value={selectedColumn}
                  onChange={(e) => setSelectedColumn(e.target.value)}
                  disabled={loading}
                >
                  <option value="">Select Column...</option>
                  {forecastColumns.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group info-group">
                <label>Available Years in Data:</label>
                <div className="years-display">
                  {years.length > 0 ? years.join(', ') : 'No data available'}
                </div>
                <small>Forecast will be generated for the next 2 years after your latest data</small>
              </div>
            </div>
            
            <button 
              className="generate-btn"
              onClick={generateForecast}
              disabled={loading || !selectedCompany || !selectedProduct || !selectedColumn}
            >
              {loading ? 'Generating...' : 'Generate 2-Year Forecast'}
            </button>

            <button 
              className="go-catalog-btn" 
              onClick={() => navigate('/analysis-catalog')}
              disabled={loading}
            >
              Go to Catalog
            </button>
          </div>
        </div>
      )}

      {step === 2 && forecastResults && (
        <div className="forecast-results">
          <div className="results-header">
            <h2>2-Year Forecast Results</h2>
            <div className="forecast-info">
              <span><strong>Company:</strong> {forecastResults.company_name}</span>
              <span><strong>Product:</strong> {forecastResults.product_name}</span>
              <span><strong>Column:</strong> {forecastResults.forecast_column}</span>
              <span><strong>Forecast Years:</strong> {forecastResults.forecast_years.join(', ')}</span>
              <span><strong>Latest Data Year:</strong> {forecastResults.trend_analysis.latest_year}</span>
            </div>
            <button className="back-btn" onClick={() => setStep(1)}>← Back to Form</button>
          </div>

          {/* Historical vs Forecast Chart */}
          <div className="chart-section">
            <h3>Historical Data & 2-Year Forecast</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={combinedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="actual" stroke="#8884d8" name="Actual" strokeWidth={2} />
                <Line type="monotone" dataKey="linear" stroke="#82ca9d" name="Linear Model" strokeDasharray="5 5" />
                <Line type="monotone" dataKey="polynomial" stroke="#ffc658" name="Polynomial Model" strokeDasharray="5 5" />
                {historicalData[0]?.prophet && (
                  <Line type="monotone" dataKey="prophet" stroke="#8dd1e1" name="Prophet Model" strokeDasharray="3 3" />
                )}
                <Line type="monotone" dataKey="forecast" stroke="#ff7300" name="2-Year Forecast" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Yearly Forecast Summary */}
          <div className="chart-section">
            <h3>Yearly Forecast Summary</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={yearlyForecastData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip formatter={(value, name) => [value.toFixed(2), name === 'total' ? 'Total' : 'Monthly Average']} />
                <Legend />
                <Bar dataKey="total" fill="#8884d8" name="Total" />
                <Bar dataKey="average" fill="#82ca9d" name="Monthly Average" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Model Performance */}
          <div className="metrics-section">
            <h3>Model Performance</h3>
            <div className="metrics-grid">
              {Object.entries(forecastResults.model_metrics).map(([modelName, metrics]) => (
                <div key={modelName} className={`metric-card ${forecastResults.forecast_data.best_model === modelName ? 'best-model' : ''}`}>
                  <h4>{modelName.charAt(0).toUpperCase() + modelName.slice(1)} Model</h4>
                  {forecastResults.forecast_data.best_model === modelName && <span className="best-badge">Best Model</span>}
                  <div className="metric-item">
                    <span>R² Score:</span>
                    <span>{(metrics.r2 * 100).toFixed(2)}%</span>
                  </div>
                  <div className="metric-item">
                    <span>MAE:</span>
                    <span>{metrics.mae.toFixed(2)}</span>
                  </div>
                  <div className="metric-item">
                    <span>RMSE:</span>
                    <span>{metrics.rmse.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Seasonal Analysis */}
          {seasonalData.length > 0 && (
            <div className="chart-section">
              <h3>Seasonal Pattern Analysis</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={seasonalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Detailed Trend Analysis */}
          <div className="trend-analysis">
            <h3>Detailed Trend Analysis</h3>
            <div className="analysis-grid">
              <div className="analysis-card">
                <h4>Historical Trends</h4>
                <div className="trend-item">
                  <span>Overall Trend:</span>
                  <span className={`trend-${forecastResults.trend_analysis.historical_trend}`}>
                    {forecastResults.trend_analysis.historical_trend.charAt(0).toUpperCase() + forecastResults.trend_analysis.historical_trend.slice(1)}
                  </span>
                </div>
                {forecastResults.trend_analysis.volatility !== undefined && (
                  <div className="trend-item">
                    <span>Volatility:</span>
                    <span>{forecastResults.trend_analysis.volatility}%</span>
                  </div>
                )}
                <div className="trend-item">
                  <span>Average Value:</span>
                  <span>{forecastResults.trend_analysis.average_value}</span>
                </div>
                <div className="trend-item">
                  <span>Data Points:</span>
                  <span>{forecastResults.trend_analysis.total_data_points}</span>
                </div>
              </div>

              <div className="analysis-card">
                <h4>2-Year Forecast Summary</h4>
                <div className="trend-item">
                  <span>24-Month Total:</span>
                  <span>{forecastResults.trend_analysis.forecast_total_24_months}</span>
                </div>
                <div className="trend-item">
                  <span>Monthly Average:</span>
                  <span>{forecastResults.trend_analysis.forecast_average_monthly}</span>
                </div>
                <div className="trend-item">
                  <span>Best Model:</span>
                  <span>{forecastResults.forecast_data.best_model}</span>
                </div>
                
                <div className="yearly-breakdown">
                  <strong>Year-wise Breakdown:</strong>
                  {Object.entries(forecastResults.trend_analysis.year_wise_forecasts).map(([year, data]) => (
                    <div key={year} className="year-item">
                      <span>{year}:</span>
                      <span>Total: {data.total}, Avg: {data.average}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="analysis-card">
                <h4>Seasonal Insights</h4>
                <div className="seasonal-lists">
                  <div>
                    <strong>Peak Months:</strong>
                    <ul>
                      {forecastResults.trend_analysis.peak_months.map(month => (
                        <li key={month.month}>{month.month_name}: {month.value}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <strong>Low Months:</strong>
                    <ul>
                      {forecastResults.trend_analysis.low_months.map(month => (
                        <li key={month.month}>{month.month_name}: {month.value}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Prophet Insights (if available) */}
          {forecastResults.prophet_available && forecastResults.trend_analysis.prophet_insights && (
            <div className="analysis-card">
              <h4>Advanced Time Series Insights (Prophet Model)</h4>
              <div className="trend-item">
                <span>Trend Direction:</span>
                <span>{forecastResults.trend_analysis.prophet_insights.trend_direction}</span>
              </div>
              <div className="trend-item">
                <span>Seasonality Strength:</span>
                <span>{forecastResults.trend_analysis.prophet_insights.seasonality_strength?.toFixed(2) || 'N/A'}</span>
              </div>
              {forecastResults.trend_analysis.prophet_insights.uncertainty_range && (
                <div className="trend-item">
                  <span>Forecast Uncertainty:</span>
                  <span>±{forecastResults.trend_analysis.prophet_insights.uncertainty_range.avg_width?.toFixed(2) || 'N/A'}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ForecastPage;