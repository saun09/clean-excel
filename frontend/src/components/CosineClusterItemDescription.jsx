import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './css/CosineSimilarity.css';
import { useLocation } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

const CosineClusterItemDescription = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get filename from multiple sources with fallback
  const [cleanedFilename, setCleanedFilename] = useState(null);
  const selectedColumn = "Item_Description";

  const [threshold, setThreshold] = useState(0.8);
  const [clusteredData, setClusteredData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadLink, setDownloadLink] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  // Initialize filename on component mount
  useEffect(() => {
    const filename = location.state?.cleanedFilename || 
                    sessionStorage.getItem("df_cleaned") || 
                    sessionStorage.getItem("cleaned_filename");
    
    console.log("Available filename sources:", {
      locationState: location.state?.cleanedFilename,
      sessionDfCleaned: sessionStorage.getItem("df_cleaned"),
      sessionCleanedFilename: sessionStorage.getItem("cleaned_filename")
    });
    
    setCleanedFilename(filename);
  }, [location.state]);

  const handleRunClustering = async () => {
    setLoading(true);
    setError('');
    setClusteredData([]);
    setSuggestions([]);

    // Validation checks
    if (!cleanedFilename) {
      setError("No cleaned file found. Please upload and clean a file first.");
      setLoading(false);
      return;
    }

    if (isNaN(threshold) || threshold < 0 || threshold > 1) {
      setError("Threshold must be a number between 0 and 1.");
      setLoading(false);
      return;
    }

    // Prepare payload
    const payload = {
      filename: cleanedFilename,
      column: selectedColumn,
      threshold: Number(threshold)
    };
    
    console.log("Sending clustering request with payload:", payload);

    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/cosine_cluster`, payload, { 
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log("Clustering Response:", response.data);
      
      if (response.data.success) {
        setClusteredData(response.data.clustered_preview || []);
        setDownloadLink(`${process.env.REACT_APP_BACKEND_URL}/api/download/${response.data.output_file}`);
        setSuggestions(response.data.replacement_suggestions || []);
        
        // Update session storage with the progressive filename for next steps
        if (response.data.final_filename) {
          sessionStorage.setItem("df_cleaned", response.data.final_filename);
        }
      } else {
        setError(response.data.message || "Clustering failed");
      }
    } catch (err) {
      console.error("Clustering error:", err);
      
      if (err.response) {
        // Server responded with error status
        const errorMessage = err.response.data?.error || 
                            err.response.data?.message || 
                            `Server Error (${err.response.status})`;
        console.error("Server Error Details:", {
          status: err.response.status,
          data: err.response.data,
          headers: err.response.headers
        });
        setError(errorMessage);
      } else if (err.request) {
        // Request was made but no response received
        console.error("Network Error:", err.request);
        setError("Network error: Unable to reach server. Is the backend running on port 5000?");
      } else {
        // Something else happened
        console.error("Request Error:", err.message);
        setError(`Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptSuggestion = async (suggestion) => {
    try {
      const payload = {
        filename: cleanedFilename,
        column: selectedColumn,
        targetRow: suggestion.row,
        newValue: suggestion.suggested_value
      };

      console.log("Applying suggestion with payload:", payload);

      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/apply_replacement`, payload, { 
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // Re-run clustering to get updated data
      handleRunClustering();
    } catch (err) {
      console.error("Error applying suggestion:", err);
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.message || 
                          "Failed to apply suggestion.";
      setError(errorMessage);
    }
  };

  // Show loading or error state if no filename is available
  if (cleanedFilename === null) {
    return (
      <div className="cosine-similarity-container">
        <div className="header-section">
          <h2>Cosine Similarity Clustering - ITEM DESCRIPTION</h2>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!cleanedFilename) {
    return (
      <div className="cosine-similarity-container">
        <div className="header-section">
          <h2>Cosine Similarity Clustering - ITEM DESCRIPTION</h2>
          <div className="error-message">
            ⚠️ No cleaned file found. Please upload and clean a file first.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cosine-similarity-container">
      <div className="header-section">
        <h2>Cosine Similarity Clustering - ITEM DESCRIPTION</h2>
        <p>Apply advanced clustering on text columns using TF-IDF + Cosine Similarity to find similar entries.</p>
        <div className="file-info">
          <small>Working with file: <strong>{cleanedFilename}</strong></small>
        </div>
      </div>

      <div className="clustering-controls">
        <div className="control-group">
          <label className="control-label">Similarity Threshold</label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
            className="control-input"
          />
        </div>
        <button 
          onClick={handleRunClustering} 
          disabled={loading || !cleanedFilename} 
          className="run-button"
        >
          {loading ? (
            <span className="loading-text">
              <span className="spinner"></span> Clustering...
            </span>
          ) : (
            "Run Cosine Clustering"
          )}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {clusteredData.length > 0 && (
        <>
          <div className="results-section">
            <div className="clustered-preview-card">
              <h3>Clustered Preview</h3>
              <div className="scrollable-table-container">
                <table className="preview-table">
                  <thead>
                    <tr>
                      {Object.keys(clusteredData[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {clusteredData.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((val, j) => (
                          <td key={j}>{val}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {suggestions.length > 0 && (
            <div className="suggestions-section">
              <h3>Suggested Replacements</h3>
              <div className="suggestions-table-container">
                <table className="suggestions-table">
                  <thead>
                    <tr>
                      <th>Row</th>
                      <th>Current Value</th>
                      <th>Suggested Value</th>
                      <th>Reference Row</th>
                      <th>Similarity</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {suggestions.map((sug, index) => (
                      <tr key={`${sug.replace?.row || index}-${sug.replace?.suggested_with_row || index}`} className="suggestion-row">
                        <td className="row-number">{sug.replace?.row}</td>
                        <td className="current-value">
                          <span className="value-text">{sug.replace?.original}</span>
                        </td>
                        <td className="suggested-value">
                          <span className="value-text">{sug.replace?.suggested_value}</span>
                        </td>
                        <td className="reference-row">{sug.replace?.suggested_with_row}</td>
                        <td className="similarity-score">
                          <span className="similarity-badge">
                            {sug.replace?.similarity ? (sug.replace.similarity * 100).toFixed(1) : 0}%
                          </span>
                        </td>
                        <td className="action-cell">
                          <button 
                            onClick={() => handleAcceptSuggestion(sug.replace)} 
                            className="accept-button"
                            disabled={!sug.replace}
                          >
                            ✓ Accept
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="button-row">
            {downloadLink && (
              <a className="download-link primary" href={downloadLink} download>
                Download Clustered CSV
              </a>
            )}
            
            <button onClick={() => navigate('/cluster/importer-name')}>
              Next → Importer Name
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default CosineClusterItemDescription;