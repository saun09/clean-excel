import React, { useState, useEffect } from 'react';
import './css/CompanyAnalysis.css';
import { useNavigate } from 'react-router-dom';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const CompanyAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [companyData, setCompanyData] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const clusteredFilename = sessionStorage.getItem("finalClusteredFilename");

  useEffect(() => {
    if (clusteredFilename) {
      loadCompanies();
    }
  }, [clusteredFilename]);

  const loadCompanies = async () => {
    if (!clusteredFilename) {
      setError('No clustered file found. Please go to FilterPage first.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/load-companies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: clusteredFilename
        })
      });

      const data = await response.json();

      if (data.success) {
        setCompanies(data.companies);
      } else {
        setError(data.error || 'Failed to load companies');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const analyzeCompany = async () => {
    if (!selectedCompany) {
      setError('Please select a company');
      return;
    }

    setLoading(true);
    setError('');
    setShowAnalysis(false);

    try {
      const response = await fetch('/api/analyze-company', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: clusteredFilename,
          company_name: selectedCompany
        })
      });

      const data = await response.json();

      if (data.success) {
        setCompanyData(data.records);
        setAnalysisResults(data.analysis);
        setShowAnalysis(true);
      } else {
        setError(data.error || 'Failed to analyze company');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const exportData = async () => {
    if (!selectedCompany) return;

    try {
      const response = await fetch('/api/export-company-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: clusteredFilename,
          company_name: selectedCompany
        })
      });

      const data = await response.json();

      if (data.success) {
        alert(`Data exported successfully! ${data.records_exported} records exported.`);
      } else {
        setError(data.error || 'Export failed');
      }
    } catch (err) {
      setError('Export error: ' + err.message);
    }
  };

  const filteredCompanies = companies.filter(company =>
    company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderAnalysisCard = (title, data, type) => {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
      return null;
    }




  return (
    <div className="analysis-card">
      <h3>{title}</h3>
      <div className="card-content">
        {type === 'basic' && (
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Total Transactions:</span>
              <span className="stat-value">{data.total_transactions}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Unique Importers:</span>
              <span className="stat-value">{data.unique_importers}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Unique Products:</span>
              <span className="stat-value">{data.unique_products}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Date Range:</span>
              <span className="stat-value">
                {data.date_range.start} to {data.date_range.end}
              </span>
            </div>
          </div>
        )}

        {type === 'financial' && (
          <div className="financial-grid">
            {Object.entries(data).map(([key, values]) => (
              <div key={key} className="financial-item">
                <h4>{key.replace('_', ' ').toUpperCase()}</h4>
                <div className="financial-stats">
                  <span>Total: {values.total?.toLocaleString()}</span>
                  <span>Average: {values.average?.toLocaleString()}</span>
                  <span>Max: {values.max?.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {type === 'list' && (
          <div className="list-container">
            {Object.entries(data).slice(0, 10).map(([item, count], index) => (
              <div key={index} className="list-item">
                <span className="item-name">{item}</span>
                <span className="item-count">{count}</span>
              </div>
            ))}
          </div>
        )}

        {type === 'trade' && (
          <div className="trade-patterns">
            {data.by_trade_type && (
              <div>
                <h4>Trade Type Distribution:</h4>
                {Object.entries(data.by_trade_type).map(([type, count]) => (
                  <div key={type} className="trade-item">
                    <span>{type}:</span>
                    <span className="trade-count">{count}</span>
                  </div>
                ))}
              </div>
            )}
            {data.primary_trade_type && (
              <div className="primary-trade">
                <strong>Primary Trade Type: {data.primary_trade_type}</strong>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
const resetSelection = () => {
  setSelectedCompany('');
  setCompanyData([]);
  setAnalysisResults(null);
  setShowAnalysis(false);
  setSearchTerm('');
};

  return (
      <div className="page-wrapper">
    <div className="company-analysis">
      <div className="header">
        <h1>Company Analysis</h1>
        <p>Select a company to view detailed analysis and records</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="company-selection">
      

        <div className="select-container">
          <select
            value={selectedCompany}
            onChange={(e) => setSelectedCompany(e.target.value)}
            className="company-select"
          >
            <option value="">Select a company...</option>
            {filteredCompanies.map((company, index) => (
              <option key={index} value={company}>
                {company}
              </option>
            ))}
          </select>
          <div className="company-count">
            {filteredCompanies.length} companies available
          </div>
        </div>

        <div className="action-buttons">
          <button
            onClick={analyzeCompany}
            disabled={!selectedCompany || loading}
            className="analyze-btn"
          >
            {loading ? 'Analyzing...' : 'Analyze Company'}
          </button>
        </div>
      
      </div>

      {showAnalysis && analysisResults && (
        <div className="analysis-section">
          <h2>Analysis for: {selectedCompany}</h2>
          <div className="button-row">
  <button onClick={resetSelection} className="reset-btn">
    Select Another Company
  </button>
  <button className="go-catalog-btn" onClick={() => navigate('/analysis-catalog')}>
    Go to Catalog
  </button>
</div>


          
          <div className="analysis-grid">
            {renderAnalysisCard('Basic Statistics', analysisResults.basic_stats, 'basic')}
            {renderAnalysisCard('Trade Patterns', analysisResults.trade_patterns, 'trade')}
            {renderAnalysisCard('Financial Insights', analysisResults.financial_insights, 'financial')}
            {renderAnalysisCard('Top Importer Cities', analysisResults.geographic_analysis?.top_importer_cities, 'list')}
            {renderAnalysisCard('Top Products', analysisResults.product_analysis?.top_products, 'list')}
            {renderAnalysisCard('Top HS Codes', analysisResults.product_analysis?.top_hscodes, 'list')}
          </div>
        </div>
      )}

      {companyData.length > 0 && (
        <div className="data-section">
          <h2>Company Records ({companyData.length} shown)</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  {Object.keys(companyData[0] || {}).map((key) => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {companyData.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, cellIndex) => (
                      <td key={cellIndex}>
                        {typeof value === 'number' ? value.toLocaleString() : String(value)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
    </div>
  );
};

export default CompanyAnalysis;