import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import './css/ClusterAnalysisPage.css';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const ClusterAnalysisPage = () => {
  const navigate = useNavigate();
  const [availableColumns, setAvailableColumns] = useState([]);
  const [numericColumns, setNumericColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dataInfo, setDataInfo] = useState(null);
  const [clusterResults, setClusterResults] = useState(null);
  const [nClusters, setNClusters] = useState(5);
  const [currentStep, setCurrentStep] = useState(1);

  const targetColumns = ['Type', 'Importer_Name', 'Country_of_Origin', 'Month', 'CTH_HSCODE', 'Item_Description'];

  useEffect(() => {
    loadColumnHeaders();
  }, []);

  const loadColumnHeaders = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/get-column-headers');
      const data = await response.json();
      
      if (data.success) {
        setAvailableColumns(data.columns);
        setNumericColumns(data.numeric_columns);
        setDataInfo({
          filename: data.filename,
          rows: data.rows,
          totalColumns: data.columns.length
        });
        
        // Auto-select available target columns
        const presentTargetColumns = targetColumns.filter(col => 
          data.columns.includes(col)
        );
        setSelectedColumns(presentTargetColumns);
      } else {
        setError(data.error || 'Failed to load data');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleColumnToggle = (column) => {
    setSelectedColumns(prev => {
      if (prev.includes(column)) {
        return prev.filter(col => col !== column);
      } else {
        return [...prev, column];
      }
    });
  };

  const performAnalysis = async () => {
    if (selectedColumns.length === 0) {
      setError('Please select at least one column');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/perform-cluster-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: dataInfo.filename,
          columns: selectedColumns,
          n_clusters: nClusters
        })
      });

      const data = await response.json();
      if (data.success) {
        setClusterResults(data);
        sessionStorage.setItem('finalClusteredFilename', data.clustered_filename);
        setCurrentStep(2);
      } else {
        setError(data.error || 'Failed to perform analysis');
      }
    } catch (err) {
      setError('Failed to perform analysis');
    } finally {
      setLoading(false);
    }
  };

  const navigateToFilter = () => {
    navigate('/filter');
  };

  const renderStepIndicator = () => (
    <div className="step-indicator">
      <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
        <span className="step-number">1</span>
        <span className="step-text">Select Data</span>
      </div>
      <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
        <span className="step-number">2</span>
        <span className="step-text">View Results</span>
      </div>
    </div>
  );

  const renderColumnSelection = () => (
    <div className="selection-container">
      <div className="data-overview">
        <h3>Your Data Overview</h3>
        {dataInfo && (
          <div className="data-stats">
            <div className="stat-card">
              <div className="stat-number">{dataInfo.rows.toLocaleString()}</div>
              <div className="stat-label">Total Records</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{selectedColumns.length}</div>
              <div className="stat-label">Columns Selected</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{nClusters}</div>
              <div className="stat-label">Groups to Find</div>
            </div>
          </div>
        )}
      </div>

      <div className="column-selection">
        <div className="recommended-columns">
          <h4>Recommended for Trade Analysis</h4>
          <p>These columns work well for finding patterns in trade data</p>
          <div className="column-grid">
            {targetColumns.map(column => {
              const isAvailable = availableColumns.includes(column);
              const isSelected = selectedColumns.includes(column);
              const isNumeric = numericColumns.includes(column);
              return (
                <div key={column} className={`column-card ${isAvailable ? 'available' : 'unavailable'} ${isSelected ? 'selected' : ''}`}>
                  <label className="column-label">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleColumnToggle(column)}
                      disabled={!isAvailable}
                    />
                    <div className="column-info">
                      <span className="column-name">{column}</span>
                      {isNumeric && <span className="numeric-badge">Numbers</span>}
                      {!isAvailable && <span className="missing-badge">Not Available</span>}
                    </div>
                  </label>
                </div>
              );
            })}
          </div>
        </div>

        <div className="all-columns">
          <h4> All Available Columns</h4>
          <div className="column-list">
            {availableColumns.map(column => {
              const isSelected = selectedColumns.includes(column);
              const isNumeric = numericColumns.includes(column);
              return (
                <div key={column} className={`column-item ${isSelected ? 'selected' : ''}`}>
                  <label>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleColumnToggle(column)}
                    />
                    <span className="column-name">{column}</span>
                    {isNumeric && <span className="numeric-badge">Numbers</span>}
                  </label>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="analysis-settings">
        <h4>Analysis Settings</h4>
        <div className="setting-group">
          <label>How many groups do you want to find?</label>
          <select value={nClusters} onChange={(e) => setNClusters(parseInt(e.target.value))}>
            <option value={3}>3 Groups</option>
            <option value={4}>4 Groups</option>
            <option value={5}>5 Groups</option>
            <option value={6}>6 Groups</option>
            <option value={7}>7 Groups</option>
            <option value={8}>8 Groups</option>
          </select>
        </div>
      </div>

      <div className="action-panel">
        <button 
          className="btn btn-primary"
          onClick={performAnalysis}
          disabled={selectedColumns.length === 0 || loading}
        >
          {loading ? 'Analyzing Your Data...' : '🔍 Analyze My Data'}
        </button>
      </div>
    </div>
  );

  const getPieChartColors = (index) => {
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#87d068', '#ffb347'];
    return colors[index % colors.length];
  };

  const renderResults = () => (
    <div className="results-container">
      <div className="results-header">
        <h3> Your Data Analysis Results</h3>
        <p>We found {clusterResults?.n_clusters} distinct groups in your data</p>
      </div>

      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon"></div>
          <div className="card-content">
            <div className="card-number">{clusterResults?.n_clusters}</div>
            <div className="card-label">Groups Found</div>
          </div>
        </div>
        <div className="summary-card">
          <div className="card-icon"></div>
          <div className="card-content">
            <div className="card-number">{clusterResults?.total_records?.toLocaleString()}</div>
            <div className="card-label">Records Analyzed</div>
          </div>
        </div>
        <div className="summary-card">
          <div className="card-icon"></div>
          <div className="card-content">
            <div className="card-number">{clusterResults?.features_used?.length}</div>
            <div className="card-label">Data Fields Used</div>
          </div>
        </div>
      </div>

      {/* Group Size Distribution */}
      <div className="chart-section">
        <h4>Group Size Distribution</h4>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={clusterResults?.cluster_summary?.map(cluster => ({
                  name: `Group ${cluster.cluster_id + 1}`,
                  value: cluster.size,
                  percentage: cluster.percentage
                }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({name, percentage}) => `${name}: ${percentage}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {clusterResults?.cluster_summary?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getPieChartColors(index)} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trend Analysis */}
      {clusterResults?.trend_analysis && (
        <div className="chart-section">
          <h4> Monthly Trends by Group</h4>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={clusterResults.trend_analysis}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                {[...new Set(clusterResults.trend_analysis.map(d => d.cluster))].map(cluster => (
                  <Line 
                    key={cluster}
                    type="monotone" 
                    dataKey="count" 
                    stroke={getPieChartColors(cluster)}
                    name={`Group ${cluster + 1}`}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Overall Statistics */}
      {clusterResults?.overall_statistics && Object.keys(clusterResults.overall_statistics).length > 0 && (
        <div className="stats-section">
          <h4>Overall Statistics</h4>
          <div className="stats-grid">
            {Object.entries(clusterResults.overall_statistics).map(([column, stats]) => (
              <div key={column} className="stat-card">
                <h5>{column}</h5>
                <div className="stat-details">
                  <div className="stat-item">
                    <span className="stat-label">Total:</span>
                    <span className="stat-value">{stats.total.toLocaleString()}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Average:</span>
                    <span className="stat-value">{stats.average.toLocaleString()}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Records:</span>
                    <span className="stat-value">{stats.count.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Group Details */}
      <div className="groups-section">
        <h4> Group Characteristics</h4>
        <div className="group-cards">
          {clusterResults?.cluster_summary?.map((cluster, index) => (
            <div key={cluster.cluster_id} className="group-card">
              <div className="group-header">
                <div className="group-title">
                  <span className="group-color" style={{backgroundColor: getPieChartColors(index)}}></span>
                  <h5>Group {cluster.cluster_id + 1}</h5>
                </div>
                <div className="group-size">
                  {cluster.size.toLocaleString()} records ({cluster.percentage}%)
                </div>
              </div>
              
              <div className="group-details">
                {Object.entries(cluster.characteristics).map(([feature, data]) => (
                  <div key={feature} className="characteristic">
                    <div className="char-header">{feature}</div>
                    {data.type === 'numeric' ? (
                      <div className="numeric-stats">
                        <div className="stat-row">
                          <span>Total: {data.total.toLocaleString()}</span>
                          <span>Average: {data.average.toLocaleString()}</span>
                        </div>
                        <div className="stat-row">
                          <span>Min: {data.min.toLocaleString()}</span>
                          <span>Max: {data.max.toLocaleString()}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-stats">
                        <div className="top-values">
                          {data.top_values.map(item => (
                            <span key={item.value} className="value-tag">
                              {item.value}: {item.count}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="action-panel">
        <button className="btn btn-secondary" onClick={() => setCurrentStep(1)}>
          ← Back to Selection
        </button>
        <button className="btn btn-success" onClick={navigateToFilter}>
          Continue to Filter Analysis →
        </button>
      </div>
    </div>
  );

  return (
    <div className="cluster-analysis-page">
      <div className="page-header">
        <h1> Smart Data Grouping</h1>
        <p>Find hidden patterns and groups in your trade data - no technical knowledge required!</p>
      </div>

      {renderStepIndicator()}

      {error && (
        <div className="error-banner">
          <span> {error}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      <div className="content-area">
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <div className="loading-text">Analyzing your data...</div>
          </div>
        )}

        {currentStep === 1 && renderColumnSelection()}
        {currentStep === 2 && renderResults()}
      </div>
    </div>
  );
};

export default ClusterAnalysisPage;