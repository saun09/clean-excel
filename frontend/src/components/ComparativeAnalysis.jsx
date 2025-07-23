import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './css/ComparativeAnalysis.css';
import Select from 'react-select';
import { useNavigate } from 'react-router-dom';
import Plot from 'react-plotly.js';

const ComparativeAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const navigate = useNavigate();
  const clusteredFilename = sessionStorage.getItem("finalClusteredFilename");

  const [options, setOptions] = useState({
    years: [],
    hscodes: [],
    itemDescriptions: []
  });

  const [selectedFilters, setSelectedFilters] = useState({
    selectedYears: [],
    timePeriodType: 'quarter',
    selectedQuarterOrMonth: 'Q1',
    selectedHscode: '',
    itemDescription1: '',
    itemDescription2: ''
  });


  const quarterOptions = [
  { label: 'All Quarters', value: 'ALL' },
  { label: 'Q1 (Jan-Mar)', value: 'Q1' },
  { label: 'Q2 (Apr-Jun)', value: 'Q2' },
  { label: 'Q3 (Jul-Sep)', value: 'Q3' },
  { label: 'Q4 (Oct-Dec)', value: 'Q4' }
];


  const monthOptions = [
    { label: 'January', value: 'JAN' },
    { label: 'February', value: 'FEB' },
    { label: 'March', value: 'MAR' },
    { label: 'April', value: 'APR' },
    { label: 'May', value: 'MAY' },
    { label: 'June', value: 'JUN' },
    { label: 'July', value: 'JUL' },
    { label: 'August', value: 'AUG' },
    { label: 'September', value: 'SEP' },
    { label: 'October', value: 'OCT' },
    { label: 'November', value: 'NOV' },
    { label: 'December', value: 'DEC' }
  ];

  const timePeriodOptions = [
    { label: 'Quarter', value: 'quarter' },
    { label: 'Month', value: 'month' }
  ];

  useEffect(() => {
    if (clusteredFilename) {
      loadOptions();
    } else {
      setError('No clustered data found. Please complete clustering first.');
    }
  }, [clusteredFilename]);

  const loadOptions = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await axios.post('http://localhost:5000/api/load-comparative-options', {
        filename: clusteredFilename
      });

      if (response.data?.success) {
        const loadedOptions = response.data.options;
        setOptions({
          years: loadedOptions.years || [],
          hscodes: loadedOptions.hscodes || [],
          itemDescriptions: loadedOptions.item_descriptions || []
        });
      } else {
        setError(response.data?.error || 'Failed to load options');
      }
    } catch (err) {
      console.error('Error loading options:', err);
      setError('Failed to load comparative analysis options');
    } finally {
      setLoading(false);
    }
  };

  const getSelectOptions = (list) =>
    list.map(option => ({ label: option, value: option }));

  const handleMultiYearChange = (selectedOptions) => {
    const values = selectedOptions ? selectedOptions.map(option => option.value) : [];
    setSelectedFilters(prev => ({
      ...prev,
      selectedYears: values
    }));
  };

  const handleSingleChange = (name, selectedOption) => {
    setSelectedFilters(prev => ({
      ...prev,
      [name]: selectedOption ? selectedOption.value : ''
    }));
  };

  const handleTimePeriodChange = (selectedOption) => {
    setSelectedFilters(prev => ({
      ...prev,
      timePeriodType: selectedOption.value,
      selectedQuarterOrMonth: selectedOption.value === 'quarter' ? 'ALL' : 'JAN'

    }));
  };

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError('');
      setAnalysisResults(null);

      const payload = {
        filename: clusteredFilename,
        selected_years: selectedFilters.selectedYears,
        time_period_type: selectedFilters.timePeriodType,
        selected_quarter_or_month: selectedFilters.selectedQuarterOrMonth,
        selected_hscode: selectedFilters.selectedHscode,
        item_description_1: selectedFilters.itemDescription1,
        item_description_2: selectedFilters.itemDescription2
      };

      console.log('Sending comparative analysis payload:', payload);

      const response = await axios.post('http://localhost:5000/api/perform-comparative-analysis', payload, {
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (response.data?.success) {
        setAnalysisResults(response.data.results);
        setError('');
        console.log(' Comparative analysis completed');
      } else {
        setError(response.data?.error || 'Analysis failed');
      }

    } catch (err) {
      console.error(' Comparative analysis failed:', err);
      setError(err.response?.data?.error || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const isAnalyzeDisabled = () => {
    return loading || 
           selectedFilters.selectedYears.length === 0 || 
           !selectedFilters.selectedHscode || 
           !selectedFilters.itemDescription1 || 
           !selectedFilters.itemDescription2 ||
           selectedFilters.itemDescription1 === selectedFilters.itemDescription2;
  };

  const renderComparisonChart = () => {
    if (!analysisResults?.summary) return null;

    const item1Data = analysisResults.summary.item_1.years_data;
    const item2Data = analysisResults.summary.item_2.years_data;

    if (!item1Data.length && !item2Data.length) return null;

    return (
      <div className="comparison-chart">
        <h4>Quantity Comparison Chart</h4>
        <Plot
          data={[
            {
              x: item1Data.map(d => d.year),
              y: item1Data.map(d => d.Quantity),
              type: 'scatter',
              mode: 'lines+markers',
              name: analysisResults.summary.item_1.name,
              line: { color: '#2196F3', width: 3 },
              marker: { size: 8 }
            },
            {
              x: item2Data.map(d => d.year),
              y: item2Data.map(d => d.Quantity),
              type: 'scatter',
              mode: 'lines+markers',
              name: analysisResults.summary.item_2.name,
              line: { color: '#FF5722', width: 3 },
              marker: { size: 8 }
            }
          ]}
          layout={{
            width: 800,
            height: 500,
            title: 'Year-wise Quantity Comparison',
            xaxis: { 
              title: 'Year',
              tickmode: 'linear',
              dtick: 1
            },
            yaxis: { title: 'Quantity' },
            legend: { 
              x: 0.02, 
              y: 0.98,
              bgcolor: 'rgba(255,255,255,0.8)',
              bordercolor: '#000',
              borderwidth: 1
            },
            hovermode: 'x unified'
          }}
        />
      </div>
    );
  };

  const renderComparisonTable = () => {
    if (!analysisResults?.summary) return null;

    const item1Data = analysisResults.summary.item_1.years_data;
    const item2Data = analysisResults.summary.item_2.years_data;

    // Create a combined table with years as rows
    const allYears = [...new Set([
      ...item1Data.map(d => d.year),
      ...item2Data.map(d => d.year)
    ])].sort();

    return (
      <div className="comparison-table">
        <h4>Year-wise Comparison Table</h4>
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th>{analysisResults.summary.item_1.name}</th>
              <th>{analysisResults.summary.item_2.name}</th>
              <th>Difference</th>
              <th>Percentage Change</th>
            </tr>
          </thead>
          <tbody>
            {allYears.map(year => {
              const item1Qty = item1Data.find(d => d.year === year)?.Quantity || 0;
              const item2Qty = item2Data.find(d => d.year === year)?.Quantity || 0;
              const difference = item1Qty - item2Qty;
              const percentageChange = item2Qty !== 0 ? ((difference / item2Qty) * 100).toFixed(2) : 'N/A';

              return (
                <tr key={year}>
                  <td>{year}</td>
                  <td>{item1Qty.toLocaleString()}</td>
                  <td>{item2Qty.toLocaleString()}</td>
                  <td className={difference >= 0 ? 'positive' : 'negative'}>
                    {difference >= 0 ? '+' : ''}{difference.toLocaleString()}
                  </td>
                  <td className={difference >= 0 ? 'positive' : 'negative'}>
                    {percentageChange !== 'N/A' ? `${difference >= 0 ? '+' : ''}${percentageChange}%` : 'N/A'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="comparative-analysis-container">
      <h2>Comparative Analysis</h2>
      
      <div style={{ marginBottom: '1rem' }}>
        <button className="go-catalog-btn" onClick={() => navigate('/analysis-catalog')}>
          Go to Catalog
        </button>
      </div>

      {error && !analysisResults && <div className="error-message">{error}</div>}

      <div className="analysis-form">
        <div className="form-row">
          <div className="form-group">
            <label>Select Years *</label>
            <Select
              isMulti
              name="selectedYears"
              options={getSelectOptions(options.years)}
              value={selectedFilters.selectedYears.map(year => ({ label: year, value: year }))}
              onChange={handleMultiYearChange}
              isDisabled={loading || options.years.length === 0}
              placeholder={options.years.length === 0 ? 'No years available' : 'Select years...'}
            />
          </div>

          <div className="form-group">
            <label>Time Period Type *</label>
            <Select
              name="timePeriodType"
              options={timePeriodOptions}
              value={timePeriodOptions.find(opt => opt.value === selectedFilters.timePeriodType)}
              onChange={handleTimePeriodChange}
              isDisabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Select {selectedFilters.timePeriodType} *</label>
            <Select
              name="selectedQuarterOrMonth"
              options={selectedFilters.timePeriodType === 'quarter' ? quarterOptions : monthOptions}
              value={(selectedFilters.timePeriodType === 'quarter' ? quarterOptions : monthOptions)
                .find(opt => opt.value === selectedFilters.selectedQuarterOrMonth)}
              onChange={(selected) => handleSingleChange('selectedQuarterOrMonth', selected)}
              isDisabled={loading}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>HS Code *</label>
            <Select
              name="selectedHscode"
              options={getSelectOptions(options.hscodes)}
              value={selectedFilters.selectedHscode ? { label: selectedFilters.selectedHscode, value: selectedFilters.selectedHscode } : null}
              onChange={(selected) => handleSingleChange('selectedHscode', selected)}
              isDisabled={loading || options.hscodes.length === 0}
              placeholder={options.hscodes.length === 0 ? 'No HS codes available' : 'Select HS code...'}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Item Description 1 *</label>
            <Select
              name="itemDescription1"
              options={getSelectOptions(options.itemDescriptions)}
              value={selectedFilters.itemDescription1 ? { label: selectedFilters.itemDescription1, value: selectedFilters.itemDescription1 } : null}
              onChange={(selected) => handleSingleChange('itemDescription1', selected)}
              isDisabled={loading || options.itemDescriptions.length === 0}
              placeholder={options.itemDescriptions.length === 0 ? 'No items available' : 'Select first item...'}
            />
          </div>

          <div className="form-group">
            <label>Item Description 2 *</label>
            <Select
              name="itemDescription2"
              options={getSelectOptions(options.itemDescriptions.filter(item => item !== selectedFilters.itemDescription1))}
              value={selectedFilters.itemDescription2 ? { label: selectedFilters.itemDescription2, value: selectedFilters.itemDescription2 } : null}
              onChange={(selected) => handleSingleChange('itemDescription2', selected)}
              isDisabled={loading || options.itemDescriptions.length === 0 || !selectedFilters.itemDescription1}
              placeholder={!selectedFilters.itemDescription1 ? 'Select first item first' : 'Select second item...'}
            />
          </div>
        </div>

        <div className="button-group">
          <button 
            onClick={handleAnalyze} 
            disabled={isAnalyzeDisabled()}
            className="analyze-btn"
          >
            {loading ? 'Analyzing...' : 'Perform Comparative Analysis'}
          </button>
        </div>

        {selectedFilters.itemDescription1 === selectedFilters.itemDescription2 && selectedFilters.itemDescription1 && (
          <div className="warning-message">
            Please select two different items for comparison.
          </div>
        )}
      </div>

      {analysisResults && (
        <div className="analysis-results">
          <h3>Comparative Analysis Results</h3>
          
          <div className="analysis-parameters">
            <h4>Analysis Parameters</h4>
            <div className="parameters-grid">
              <div><strong>Years:</strong> {analysisResults.parameters.years.join(', ')}</div>
              <div><strong>Time Period:</strong> {analysisResults.parameters.time_period}</div>
              <div><strong>HS Code:</strong> {analysisResults.parameters.hscode}</div>
              <div><strong>Items:</strong> {analysisResults.parameters.items_compared.join(' vs ')}</div>
            </div>
          </div>

          <div className="summary-cards">
            <div className="summary-card">
              <h4>Item 1: {analysisResults.summary.item_1.name}</h4>
              <div className="summary-stat">
                <span className="stat-label">Total Quantity:</span>
                <span className="stat-value">{analysisResults.summary.item_1.total_quantity.toLocaleString()}</span>
              </div>
            </div>
            
            <div className="summary-card">
              <h4>Item 2: {analysisResults.summary.item_2.name}</h4>
              <div className="summary-stat">
                <span className="stat-label">Total Quantity:</span>
                <span className="stat-value">{analysisResults.summary.item_2.total_quantity.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {renderComparisonChart()}
          {renderComparisonTable()}
        </div>
      )}
    </div>
  );
};

export default ComparativeAnalysis;