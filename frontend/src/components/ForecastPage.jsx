import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './css/ForecastAnalysis.css';
import Plot from 'react-plotly.js';
import Select from 'react-select';

const Forecasting = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forecastResults, setForecastResults] = useState(null);
  const [forecastImage, setForecastImage] = useState(null);
  const [selectedItem, setSelectedItem] = useState('');
  const [items, setItems] = useState([]);
  const [valueColumns, setValueColumns] = useState([]);
  const [selectedValueCol, setSelectedValueCol] = useState('');
  const clusteredFilename = sessionStorage.getItem("df_clustered");

  useEffect(() => {
    if (clusteredFilename) {
      loadForecastOptions();
    } else {
      setError('No clustered data found. Please complete clustering first.');
    }
  }, [clusteredFilename]);

  const loadForecastOptions = async () => {
  try {
    setLoading(true);
    setError('');
    
    if (!clusteredFilename) {
      throw new Error('No clustered data filename found in session');
    }

    console.log('Loading forecast options for file:', clusteredFilename);
    
    const response = await axios.post('http://localhost:5000/api/load-forecast-options', {
      filename: clusteredFilename
    }, {
      timeout: 10000 // 10 second timeout
    });

    console.log('Forecast options response:', response.data);

    if (response.data?.error) {
      throw new Error(response.data.error);
    }

    const options = response.data?.options || {
      items: [],
      value_columns: []
    };

    setItems(options.items || []);
    setValueColumns(options.value_columns || []);

    if (options.value_columns?.length > 0) {
      setSelectedValueCol(options.value_columns[0]);
    }

  } catch (err) {
    console.error('Error loading forecast options:', err);
    setError(err.response?.data?.error || err.message || 'Failed to load forecast options');
    setItems([]);
    setValueColumns([]);
    
    // Log additional error details
    if (err.response) {
      console.error('Server responded with:', err.response.status, err.response.data);
    } else if (err.request) {
      console.error('No response received:', err.request);
    }
  } finally {
    setLoading(false);
  }
};

  const handleForecast = async () => {
    try {
      setLoading(true);
      setError('');
      setForecastResults(null);
      setForecastImage(null);

      if (!selectedItem || !selectedValueCol) {
        setError('Please select both an item and value column');
        return;
      }

      const payload = {
        filename: clusteredFilename,
        item_name: selectedItem,
        value_column: selectedValueCol
      };

      const response = await axios.post('http://localhost:5000/api/generate-forecast', payload, {
        headers: { 'Content-Type': 'application/json' },
        responseType: 'json'
      });

      if (response.data?.success) {
        if (response.data.forecast) {
          setForecastResults(response.data.forecast);
          if (response.data.plot_image) {
            setForecastImage(`data:image/png;base64,${response.data.plot_image}`);
          }
        } else {
          setError(response.data.message || 'Forecast completed but no results returned');
        }
      } else {
        setError(response.data?.error || 'Forecast failed');
      }
    } catch (err) {
      console.error('Forecast error:', err);
      setError(err.response?.data?.error || err.message || 'Forecast failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forecast-container">
      <h2>Time Series Forecasting</h2>
      <p className="description">
        Generate 12-month forecasts for trade items using Facebook's Prophet algorithm.
        Select an item and value column to begin.
      </p>

      {error && <div className="error-message">{error}</div>}

      <div className="forecast-form">
        <div className="form-group">
          <label>Item to Forecast *</label>
          <Select
            options={items.map(item => ({ label: item, value: item }))}
            value={selectedItem ? { label: selectedItem, value: selectedItem } : null}
            onChange={(selected) => setSelectedItem(selected?.value || '')}
            isDisabled={loading || items.length === 0}
            placeholder="Select an item..."
          />
        </div>

        <div className="form-group">
          <label>Value Column *</label>
          <Select
            options={valueColumns.map(col => ({ label: col, value: col }))}
            value={selectedValueCol ? { label: selectedValueCol, value: selectedValueCol } : null}
            onChange={(selected) => setSelectedValueCol(selected?.value || '')}
            isDisabled={loading || valueColumns.length === 0}
            placeholder="Select a value column..."
          />
        </div>

        <button 
          onClick={handleForecast} 
          disabled={loading || !selectedItem || !selectedValueCol}
          className="forecast-button"
        >
          {loading ? 'Generating Forecast...' : 'Generate Forecast'}
        </button>
      </div>

      {forecastResults && (
        <div className="forecast-results">
          <h3>Forecast Results for {selectedItem}</h3>
          
          {forecastResults.description && (
            <div className="trend-analysis">
              <h4>Trend Analysis</h4>
              <p>{forecastResults.description}</p>
            </div>
          )}

          {forecastImage && (
            <div className="forecast-plot">
              <h4>Historical vs Forecast</h4>
              <img src={forecastImage} alt="Forecast plot" />
            </div>
          )}

          {forecastResults.forecast && (
            <div className="forecast-table">
              <h4>12-Month Forecast</h4>
              <table>
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Forecasted Value</th>
                  </tr>
                </thead>
                <tbody>
                  {forecastResults.forecast.map((row, i) => (
                    <tr key={i}>
                      <td>{new Date(row.ds).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</td>
                      <td>{row[selectedValueCol]?.toLocaleString() || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Forecasting;