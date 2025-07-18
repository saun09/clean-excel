import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './css/FilterPage.css';
import DataTable from './DataTable';
import Plot from 'react-plotly.js';
import Select from 'react-select';

const FilterPage = () => {
  const [data, setData] = useState([]);

  const [filterOptions, setFilterOptions] = useState({
    tradeTypes: [],
    importerCities: [],
    supplierCountries: [],
    numericColumns: [],
    years: [],
    hscodes: [],
    itemDescriptions: []
  });

  const [selectedFilters, setSelectedFilters] = useState({
  tradeType: [],
  importer: [],
  supplier: [],
  valueCol: '',
  years: [],
  hscode: [],
  item: []
});



  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [previewData, setPreviewData] = useState([]);
  //const clusteredFilename = sessionStorage.getItem("df_clustered");
  const clusteredFilename = sessionStorage.getItem("finalClusteredFilename");

  const [analysisResults, setAnalysisResults] = useState(null);
 const getMultiSelectOptions = (list) =>
  list.map(option => ({ label: option, value: option }));

const handleMultiChange = (name, selectedOptions) => {
  const values = selectedOptions.map(option => option.value);

  if (values.includes('All')) {
    const fullList = {
      tradeType: filterOptions.tradeTypes,
      importer: filterOptions.importerCities,
      supplier: filterOptions.supplierCountries,
    //  valueCol: filterOptions.numericColumns,
      years: filterOptions.years,
      hscode: filterOptions.hscodes,
      item: filterOptions.itemDescriptions
    }[name];

    setSelectedFilters(prev => ({
      ...prev,
      [name]: fullList
    }));
  } else {
    setSelectedFilters(prev => ({
      ...prev,
      [name]: values
    }));
  }
};



  useEffect(() => {
    if (clusteredFilename) {
      loadFilterOptions();
    } else {
      setError('No clustered data found. Please complete clustering first.');
    }
  }, [clusteredFilename]);

  const loadFilterOptions = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await axios.post('http://localhost:5000/api/load-filter-options', {
        filename: clusteredFilename
      });

      const options = response.data?.options || {
        trade_types: [],
        importer_cities: [],
        supplier_countries: [],
        numeric_columns: [],
        years: [],
        hscodes: [],
        item_descriptions: []
      };

      setFilterOptions({
        tradeTypes: options.trade_types || [],
        importerCities: options.importer_cities || [],
        supplierCountries: options.supplier_countries || [],
        numericColumns: options.numeric_columns || [],
        years: options.years || [],
        hscodes: options.hscodes || [],
        itemDescriptions: options.item_descriptions || []
      });

      if (options.numeric_columns?.length > 0) {
        setSelectedFilters(prev => ({
          ...prev,
          valueCol: options.numeric_columns[0]
        }));
      }

    } catch (err) {
      console.error('Error loading filter options:', err);
      setError('Failed to load filter options');
      setFilterOptions({
        tradeTypes: [],
        importerCities: [],
        supplierCountries: [],
        numericColumns: [],
        years: [],
        hscodes: [],
        itemDescriptions: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setSelectedFilters(prev => {
      const updated = { ...prev, [name]: value };
      console.log(`🔧 Updated filter: ${name} = ${value}`);
      return updated;
    });
  };

  const handleYearSelect = (e) => {
    const selected = Array.from(e.target.options)
      .filter(option => option.selected)
      .map(option => option.value);
    console.log('📅 Selected Years:', selected);
    setSelectedFilters(prev => ({
      ...prev,
      years: selected
    }));
  };

  const handlePreview = async () => {
    try {
      setLoading(true);
      setError('');
      setPreviewData([]);
      

      const payload = {
        filename: clusteredFilename,
        ...(selectedFilters.tradeType.length>0 && { tradeType: selectedFilters.tradeType }),
        ...(selectedFilters.importer.length > 0 && { importer: selectedFilters.importer }),
        ...(selectedFilters.supplier.length>0 && { supplier: selectedFilters.supplier}),
        ...(typeof selectedFilters.valueCol === 'string' && selectedFilters.valueCol.trim() !== '' && {
        value_col: selectedFilters.valueCol
        }),
        ...(selectedFilters.hscode && { hscode: selectedFilters.hscode.toString().trim() }),
      };
      if (Array.isArray(payload.hscode)) {
  payload.hscode = payload.hscode.join(',');  // Or just use first one: payload.hscode[0]
}

      console.log('Sending payload:', payload);
      console.log("👉 Payload value_col type:", typeof payload.value_col);
      console.log("👉 Payload value_col value:", payload.value_col);
      const response = await axios.post('http://localhost:5000/api/filter-data', payload, {
        headers: { 'Content-Type': 'application/json' }
      });

      console.log('Received response:', response.data);

      if (response.data?.success) {
        if (response.data.data.length === 0) {
          setError(`No records found with these filters. Try broadening your search.`);
        } else {
          setPreviewData(response.data.data);
        }
      } else {
        setError(response.data?.error || 'No data returned from server');
      }
    } catch (err) {
      const serverError = err.response?.data?.error;
      const validationError = err.response?.data?.message;
      setError(serverError || validationError || err.message || 'Filtering failed');
    } finally {
      setLoading(false);
    }
  };

  const renderDropdown = (label, name, options, required = false) => (
    <div className="form-group">
      <label>{label}{required && ' *'}</label>
      <select
        name={name}
        value={selectedFilters[name]}
        onChange={handleFilterChange}
        required={required}
        disabled={loading || options.length === 0}
      >
        <option value="">Select {label.split(' ')[0]}</option>
        {options.map(option => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </div>
  );
const handleAnalyze = async () => {
  try {
    setLoading(true);
    setError('');
    setAnalysisResults(null);

    const payload = {
      filename: clusteredFilename,
      ...(selectedFilters.tradeType.length>0 && { tradeType: selectedFilters.tradeType }),
      ...(selectedFilters.importer.length>0 && { importer: selectedFilters.importer }),
      ...(selectedFilters.supplier.length>0 && { supplier: selectedFilters.supplier }),
      ...(selectedFilters.hscode.length>0 && { hscode: selectedFilters.hscode }),
      ...(selectedFilters.item.length>0 && { item: selectedFilters.item }),
      ...(selectedFilters.years.length > 0 && { years: selectedFilters.years }),
      value_col: selectedFilters.valueCol
    };

    console.log('🔍 Analyzing with payload:', payload);

    const response = await axios.post('http://localhost:5000/api/analyze-filtered', payload, {
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    console.log('✅ Full Response:', response);
    console.log('✅ Response Data:', response.data);
    console.log('✅ Response Data Type:', typeof response.data);
    
    // ✅ FIXED: Parse JSON string if necessary and handle NaN values
    let parsedData;
    try {
      if (typeof response.data === 'string') {
        // Clean NaN values from the JSON string before parsing
        const cleanedJsonString = response.data
          .replace(/:\s*NaN/g, ': null')
          .replace(/:\s*-NaN/g, ': null')
          .replace(/:\s*Infinity/g, ': null')
          .replace(/:\s*-Infinity/g, ': null');
        
        parsedData = JSON.parse(cleanedJsonString);
      } else {
        parsedData = response.data;
      }
    } catch (parseError) {
      console.error('❌ Failed to parse response data:', parseError);
      console.error('❌ Raw response data:', response.data);
      throw new Error('Invalid response format from server');
    }
    
    console.log('✅ Parsed Data:', parsedData);
    
    // Extract data more defensively
    const { success, results, message } = parsedData || {};
    
    console.log('- success:', success);
    console.log('- results exists:', !!results);
    console.log('- message:', message);
    console.log('- results type:', typeof results);
    console.log('- results keys:', results ? Object.keys(results) : 'no results');

    // Check for valid results
    const hasResults = results && typeof results === 'object' && 
      Object.values(results).some(section => Array.isArray(section) && section.length > 0);

    if (success && hasResults) {
      setAnalysisResults(results);
      setError('');
      console.log('✅ Analysis results set successfully');
    } else {
      setAnalysisResults(null);
      setError(message || 'Analysis completed but no results found');
      console.log('❌ No valid results found');
    }

  } catch (err) {
    console.error('❌ Analysis failed:', err);
    setAnalysisResults(null);
    setError(err.response?.data?.error || err.message || 'Analysis failed');
    console.log("🔍 Error Response:", err.response?.data);

  }
   finally {
    setLoading(false);
  }
  
};
  return (
    <div className="filter-container">
      <h2>Filter and Analyze Trade Data</h2>
      
      {error && !analysisResults && <div className="error-message">{error}</div>}

      <div className="filter-form">
        <div className="form-group">
  <label>Trade Type</label>
  <Select
    isMulti
    name="tradeType"
    options={[{ label: 'All', value: 'All' }, ...getMultiSelectOptions(filterOptions.tradeTypes)]}
    value={selectedFilters.tradeType.map(val => ({ label: val, value: val }))}
    onChange={(selected) => handleMultiChange('tradeType', selected)}
    isDisabled={loading || filterOptions.tradeTypes.length === 0}
  />
</div>

<div className="form-group">
  <label>Importer City/State *</label>
  <Select
    isMulti
    name="importer"
    options={[{ label: 'All', value: 'All' }, ...getMultiSelectOptions(filterOptions.importerCities)]}
    value={selectedFilters.importer.map(val => ({ label: val, value: val }))}
    onChange={(selected) => handleMultiChange('importer', selected)}
    isDisabled={loading || filterOptions.importerCities.length === 0}
  />
</div>

<div className="form-group">
  <label>Supplier Country *</label>
  <Select
    isMulti
    name="supplier"
    options={[{ label: 'All', value: 'All' }, ...getMultiSelectOptions(filterOptions.supplierCountries)]}
    value={selectedFilters.supplier.map(val => ({ label: val, value: val }))}
    onChange={(selected) => handleMultiChange('supplier', selected)}
    isDisabled={loading || filterOptions.supplierCountries.length === 0}
  />
</div>

<div className = "form-group">
  <label>Value Column * </label>
<Select
  name="valueCol"
  options={getMultiSelectOptions(filterOptions.numericColumns)}
  value={selectedFilters.valueCol ? { label: selectedFilters.valueCol, value: selectedFilters.valueCol } : null}
  onChange={(selected) =>
    setSelectedFilters(prev => ({
      ...prev,
      valueCol: selected ? selected.value : ''
    }))
  }
  isDisabled={loading || filterOptions.numericColumns.length === 0}
/>
</div>


        <div className="form-group">
  <label>Years</label>
  <Select
    isMulti
    name="years"
    options={[{ label: 'All', value: 'All' }, ...filterOptions.years.map(year => ({ label: year, value: year }))]}
    value={selectedFilters.years.map(year => ({ label: year, value: year }))}
    onChange={(selectedOptions) => handleMultiChange('years', selectedOptions)}
    isDisabled={loading || filterOptions.years.length === 0}
  />
</div>

        
        <div className="form-group">
  <label>HS Code</label>
  <Select
    isMulti
    name="hscode"
    options={[{ label: 'All', value: 'All' }, ...getMultiSelectOptions(filterOptions.hscodes)]}
    value={selectedFilters.hscode.map(val => ({ label: val, value: val }))}
    onChange={(selected) => handleMultiChange('hscode', selected)}
    isDisabled={loading || filterOptions.hscodes.length === 0}
  />
</div>

<div className="form-group">
  <label>Item Description</label>
  <Select
    isMulti
    name="item"
    options={[{ label: 'All', value: 'All' }, ...getMultiSelectOptions(filterOptions.itemDescriptions)]}
    value={selectedFilters.item.map(val => ({ label: val, value: val }))}
    onChange={(selected) => handleMultiChange('item', selected)}
    isDisabled={loading || filterOptions.itemDescriptions.length === 0}
  />
</div>
        <div className="button-group">
          <button 
            onClick={handlePreview} 
            disabled={loading || !selectedFilters.importer || !selectedFilters.supplier || !selectedFilters.valueCol}
          >
            {loading ? 'Processing...' : 'Preview Data'}
          </button>
          <button 
            onClick={handleAnalyze} 
            disabled={loading || !selectedFilters.valueCol}
            className="analyze-btn"
          >
            {loading ? 'Analyzing...' : 'Perform Analysis'}
          </button>
        </div>
      </div>

      {previewData.length > 0 ? (
        <div className="preview-section">
          <h3>Filtered Data Preview ({previewData.length} rows)</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  {Object.keys(previewData[0]).map(key => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((value, j) => (
                      <td key={j}>
                        {value !== null && value !== undefined ? String(value) : '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="no-preview">
          {loading ? 'Loading preview...' : 'No preview data available'}
        </div>
      )}

      {analysisResults && (
        <div className="analysis-results">
          <h3>Trade Analysis Results</h3>
          
          {/* Summary Metrics */}
          <div className="metrics-summary">
            {analysisResults['Trend Analysis'] && (
              <div className="trend-analysis">
                <h4>Trend Analysis</h4>
                <p>{analysisResults['Trend Analysis']}</p>
              </div>
            )}
          </div>
          
          {/* Top Importers Table */}
          {analysisResults['1. Top Importer-Supplier Combinations'] && (
            <div className="analysis-section">
              <h4>Top Importer-Supplier Combinations</h4>
              <DataTable
                data={analysisResults['1. Top Importer-Supplier Combinations']}
                columns={[
                  { Header: 'Importer', accessor: 'Importer_City_State' },
                  { Header: 'Supplier', accessor: 'Country_of_Origin' },
                  { Header: 'Value', accessor: selectedFilters.valueCol || 'BE_NO' }
                ]}
              />
            </div>
          )}
          
          {/* Export Dominance */}
          {analysisResults['4. Export Dominance Share'] && (
            <div className="analysis-section">
              <h4>Export Market Share</h4>
              <DataTable
                data={analysisResults['4. Export Dominance Share']}
                columns={[
                  { Header: 'Country', accessor: 'Country_of_Origin' },
                  { Header: 'Value', accessor: selectedFilters.valueCol || 'BE_NO' },
                  { Header: 'Market Share', accessor: '% Share' }
                ]}
              />
            </div>
          )}
          
          {/* Unit Value Analysis */}
          {analysisResults['7A. Highest Avg Value per Unit'] && (
            <div className="analysis-section">
              <h4>Unit Value Analysis</h4>
              <div className="unit-value-comparison">
                <div>
                  <h5>Highest Unit Values</h5>
                  <DataTable
                    data={analysisResults['7A. Highest Avg Value per Unit']}
                    columns={[
                      { Header: 'Supplier', accessor: 'Country_of_Origin' },
                      { Header: 'Importer', accessor: 'Importer_City_State' },
                      { Header: 'Avg Value/Unit', accessor: 'Unit_Value' }
                    ]}
                  />
                </div>
                <div>
                  <h5>Lowest Unit Values</h5>
                  <DataTable
                    data={analysisResults['7B. Lowest Avg Value per Unit']}
                    columns={[
                      { Header: 'Supplier', accessor: 'Country_of_Origin' },
                      { Header: 'Importer', accessor: 'Importer_City_State' },
                      { Header: 'Avg Value/Unit', accessor: 'Unit_Value' }
                    ]}
                  />
                </div>
              </div>
            </div>
          )}
          {analysisResults['8. Importer-Supplier Heatmap Data'] && (
  <div className="analysis-section">
    <h4>Importer-Supplier Heatmap</h4>
    <Plot
      data={[
        {
          z: analysisResults['8. Importer-Supplier Heatmap Data'].map(row => 
              Object.entries(row)
                .filter(([key]) => key !== 'Importer_City_State')
                .map(([, val]) => val)
          ),
          x: Object.keys(analysisResults['8. Importer-Supplier Heatmap Data'][0]).filter(key => key !== 'Importer_City_State'),
          y: analysisResults['8. Importer-Supplier Heatmap Data'].map(row => row.Importer_City_State),
          type: 'heatmap',
          colorscale: 'Viridis',
        }
      ]}
      layout={{
        width: 700,
        height: 500,
        title: 'Trade Value Heatmap',
        xaxis: { title: 'Supplier Country' },
        yaxis: { title: 'Importer City/State' }
      }}
    />
  </div>
)}

        </div>
      )}
    </div>
  );
};

export default FilterPage;