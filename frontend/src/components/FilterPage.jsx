import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './css/FilterPage.css';
import DataTable from './DataTable';
import Plot from 'react-plotly.js';
import Select from 'react-select';
import { useNavigate } from 'react-router-dom';


const FilterPage = () => {
  const [data, setData] = useState([]);
  const [columnMappings, setColumnMappings] = useState({});
  const [availableColumns, setAvailableColumns] = useState([]);
   const navigate = useNavigate();

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
  const clusteredFilename = sessionStorage.getItem("finalClusteredFilename");
  const [analysisResults, setAnalysisResults] = useState(null);

  // Helper function to find column by possible names
  const findColumnByNames = (columns, possibleNames) => {
    for (const name of possibleNames) {
      const found = columns.find(col => 
        col.toLowerCase().includes(name.toLowerCase()) ||
        name.toLowerCase().includes(col.toLowerCase())
      );
      if (found) return found;
    }
    return null;
  };

  // Dynamic column detection
  const detectColumnMappings = (columns) => {
    const mappings = {
      importer: findColumnByNames(columns, ['Importer_City_State', 'importer', 'city', 'state', 'importer_city']),
      supplier: findColumnByNames(columns, ['Country_of_Origin', 'supplier', 'country', 'origin', 'exporter']),
      tradeType: findColumnByNames(columns, ['Type', 'trade_type', 'transaction_type']),
      hscode: findColumnByNames(columns, ['CTH_HSCODE', 'hscode', 'hs_code', 'tariff_code']),
      item: findColumnByNames(columns, ['Item_Description', 'description', 'product', 'item', 'commodity']),
      quantity: findColumnByNames(columns, ['Quantity', 'qty', 'amount', 'volume']),
      year: findColumnByNames(columns, ['YEAR', 'year']),
      month: findColumnByNames(columns, ['Month', 'month', 'date'])
    };
    
    console.log('🔍 Detected column mappings:', mappings);
    return mappings;
  };

  const getMultiSelectOptions = (list) =>
    list.map(option => ({ label: option, value: option }));

  const handleMultiChange = (name, selectedOptions) => {
    const values = selectedOptions.map(option => option.value);

    if (values.includes('All')) {
      const fullList = {
        tradeType: filterOptions.tradeTypes,
        importer: filterOptions.importerCities,
        supplier: filterOptions.supplierCountries,
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

      // Store all available columns for dynamic mapping
      if (response.data?.available_columns) {
        setAvailableColumns(response.data.available_columns);
        setColumnMappings(detectColumnMappings(response.data.available_columns));
      }

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

  const handlePreview = async () => {
    try {
      setLoading(true);
      setError('');
      setPreviewData([]);
      
      const payload = {
        filename: clusteredFilename,
        ...(selectedFilters.tradeType.length > 0 && { tradeType: selectedFilters.tradeType }),
        ...(selectedFilters.importer.length > 0 && { importer: selectedFilters.importer }),
        ...(selectedFilters.supplier.length > 0 && { supplier: selectedFilters.supplier }),
        ...(typeof selectedFilters.valueCol === 'string' && selectedFilters.valueCol.trim() !== '' && {
          value_col: selectedFilters.valueCol
        }),
        ...(selectedFilters.hscode.length > 0 && { hscode: selectedFilters.hscode }),
        ...(selectedFilters.item.length > 0 && { item: selectedFilters.item }),
        ...(selectedFilters.years.length > 0 && { years: selectedFilters.years })
      };

      console.log('Sending payload:', payload);
      
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

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError('');
      setAnalysisResults(null);

      const payload = {
        filename: clusteredFilename,
        ...(selectedFilters.tradeType.length > 0 && { tradeType: selectedFilters.tradeType }),
        ...(selectedFilters.importer.length > 0 && { importer: selectedFilters.importer }),
        ...(selectedFilters.supplier.length > 0 && { supplier: selectedFilters.supplier }),
        ...(selectedFilters.hscode.length > 0 && { hscode: selectedFilters.hscode }),
        ...(selectedFilters.item.length > 0 && { item: selectedFilters.item }),
        ...(selectedFilters.years.length > 0 && { years: selectedFilters.years }),
        value_col: selectedFilters.valueCol,
        // Send column mappings to backend for dynamic handling
        column_mappings: columnMappings
      };

      console.log('🔍 Analyzing with payload:', payload);

      const response = await axios.post('http://localhost:5000/api/analyze-filtered', payload, {
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      let parsedData;
      try {
        if (typeof response.data === 'string') {
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
        throw new Error('Invalid response format from server');
      }
      
      const { success, results, message } = parsedData || {};
      
      const hasResults = results && typeof results === 'object' && 
        Object.values(results).some(section => Array.isArray(section) && section.length > 0);

      if (success && hasResults) {
        setAnalysisResults(results);
        setError('');
        console.log('✅ Analysis results set successfully');
      } else {
        setAnalysisResults(null);
        setError(message || 'Analysis completed but no results found');
      }

    } catch (err) {
      console.error('❌ Analysis failed:', err);
      setAnalysisResults(null);
      setError(err.response?.data?.error || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  // Dynamic table column generation
  const generateTableColumns = (data, section) => {
    if (!data || data.length === 0) return [];
    
    const firstRow = data[0];
    const columns = [];

    // Map common column names dynamically
    Object.keys(firstRow).forEach(key => {
      let header = key;
      let accessor = key;

      // Transform column headers for better readability
      if (key === columnMappings.importer || key.includes('Importer') || key.includes('City')) {
        header = 'Importer';
      } else if (key === columnMappings.supplier || key.includes('Country') || key.includes('Origin')) {
        header = 'Supplier Country';
      } else if (key === selectedFilters.valueCol) {
        header = 'Trade Value';
      } else if (key.includes('Unit_Value')) {
        header = 'Value per Unit';
      } else if (key.includes('Share')) {
        header = 'Market Share (%)';
      } else if (key.includes('Change')) {
        header = 'Change (%)';
      }

      columns.push({ Header: header, accessor });
    });

    return columns;
  };

  const renderAnalysisSection = (title, data, customColumns = null) => {
    if (!data || data.length === 0) return null;

    const columns = customColumns || generateTableColumns(data, title);

    return (
      <div className="analysis-section" key={title}>
        <h4>{title}</h4>
        <DataTable
          data={data}
          columns={columns}
        />
      </div>
    );
  };

  return (
    <div className="filter-container">
      <h2>Filter and Analyze Trade Data</h2>
      <div style={{ marginBottom: '1rem' }}>
  <button className="go-catalog-btn" onClick={() => navigate('/analysis-catalog')}>
    Go to Catalog
  </button>
</div>

      
      {error && !analysisResults && <div className="error-message">{error}</div>}

      {/* Column Mapping Info */}
      {Object.keys(columnMappings).length > 0 && (
        <div className="column-info">
          <details>
            <summary>Detected Column Mappings</summary>
            <ul>
              {Object.entries(columnMappings).map(([key, value]) => (
                <li key={key}>{key}: {value || 'Not found'}</li>
              ))}
            </ul>
          </details>
        </div>
      )}

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
            placeholder={filterOptions.tradeTypes.length === 0 ? 'No trade types available' : 'Select trade types...'}
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
            placeholder={filterOptions.importerCities.length === 0 ? 'No importers available' : 'Select importers...'}
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
            placeholder={filterOptions.supplierCountries.length === 0 ? 'No suppliers available' : 'Select suppliers...'}
          />
        </div>

        <div className="form-group">
          <label>Value Column *</label>
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
            placeholder={filterOptions.numericColumns.length === 0 ? 'No numeric columns available' : 'Select value column...'}
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
            placeholder={filterOptions.years.length === 0 ? 'No years available' : 'Select years...'}
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
            placeholder={filterOptions.hscodes.length === 0 ? 'No HS codes available' : 'Select HS codes...'}
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
            placeholder={filterOptions.itemDescriptions.length === 0 ? 'No items available' : 'Select items...'}
          />
        </div>

        <div className="button-group">
          <button 
            onClick={handlePreview} 
            disabled={loading || selectedFilters.importer.length === 0 || selectedFilters.supplier.length === 0 || !selectedFilters.valueCol}
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
          
          {/* Dynamically render all analysis sections */}
          {Object.entries(analysisResults).map(([key, data]) => {
            if (key === 'Trend Analysis' || key === 'error') return null;
            
            // Special handling for heatmap
            if (key === '8. Importer-Supplier Heatmap Data' && Array.isArray(data) && data.length > 0) {
              return (
                <div className="analysis-section" key={key}>
                  <h4>Importer-Supplier Heatmap</h4>
                  <Plot
                    data={[
                      {
                        z: data.map(row => 
                          Object.entries(row)
                            .filter(([colKey]) => !colKey.includes(columnMappings.importer || 'Importer'))
                            .map(([, val]) => val)
                        ),
                        x: Object.keys(data[0]).filter(colKey => !colKey.includes(columnMappings.importer || 'Importer')),
                        y: data.map(row => row[columnMappings.importer] || row['Importer_City_State'] || Object.values(row)[0]),
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
              );
            }
            
            // Handle unit value analysis with split display
            if (key === '7A. Highest Avg Value per Unit' && analysisResults['7B. Lowest Avg Value per Unit']) {
              return (
                <div className="analysis-section" key="unit-value-analysis">
                  <h4>Unit Value Analysis</h4>
                  <div className="unit-value-comparison">
                    <div>
                      <h5>Highest Unit Values</h5>
                      <DataTable
                        data={data}
                        columns={generateTableColumns(data, key)}
                      />
                    </div>
                    <div>
                      <h5>Lowest Unit Values</h5>
                      <DataTable
                        data={analysisResults['7B. Lowest Avg Value per Unit']}
                        columns={generateTableColumns(analysisResults['7B. Lowest Avg Value per Unit'], '7B')}
                      />
                    </div>
                  </div>
                </div>
              );
            }
            
            // Skip 7B as it's handled above
            if (key === '7B. Lowest Avg Value per Unit') return null;
            
            // Regular table sections
            if (Array.isArray(data) && data.length > 0) {
              return renderAnalysisSection(key, data);
            }
            
            return null;
          })}
        </div>
      )}
    </div>
  );
};

export default FilterPage;