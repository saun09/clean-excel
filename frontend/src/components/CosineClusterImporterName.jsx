import React, { useState } from 'react';
import axios from 'axios';
import './css/CosineSimilarity.css';
import { useLocation, useNavigate } from 'react-router-dom';

const CosineClusterImporterName = () => {
  const location = useLocation();
  const cleanedFilename = location.state?.cleanedFilename || sessionStorage.getItem("df_cleaned");
  const selectedColumn = "Importer_Name";

  const [threshold, setThreshold] = useState(0.8);
  const [clusteredData, setClusteredData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadLink, setDownloadLink] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const navigate = useNavigate();

  const handleRunClustering = async () => {
    setLoading(true);
    setError('');
    setClusteredData([]);
    setSuggestions([]);

    try {
      const response = await axios.post('http://localhost:5000/api/cosine_cluster', {
        filename: cleanedFilename,
        column: selectedColumn,
        threshold
      }, { withCredentials: true });

      setClusteredData(response.data.clustered_preview || []);
      setDownloadLink(`http://localhost:5000/api/download/${response.data.output_file}`);
      setSuggestions(response.data.replacement_suggestions || []);
    } catch (err) {
      setError("Failed to run clustering. Please try again.");
    }
    setLoading(false);
  };

  const handleAcceptSuggestion = async (suggestion) => {
    try {
      await axios.post('http://localhost:5000/api/apply_replacement', {
        filename: cleanedFilename,
        column: selectedColumn,
        targetRow: suggestion.row,
        newValue: suggestion.suggested_value
      }, { withCredentials: true });

      handleRunClustering();
    } catch {
      setError("Failed to apply suggestion.");
    }
  };

  if (!cleanedFilename) {
    return <div className="cosine-similarity-container">⚠️ No cleaned file found. Please upload and clean a file first.</div>;
  }
 return (
    <div className="cosine-similarity-container">
      <div className="header-section">
        <h2>Cosine Similarity Clustering-IMPORTER NAME</h2>
        <p>Apply advanced clustering on text columns using TF-IDF + Cosine Similarity to find similar entries.</p>
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
          onChange={(e) => setThreshold(parseFloat(e.target.value))}
          className="control-input"
        />
      </div>
      <button onClick={handleRunClustering} disabled={loading} className="run-button">
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
        <div className = "results-section">
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
          <tr key={`${sug.replace.row}-${sug.replace.suggested_with_row}`} className="suggestion-row">
            <td className="row-number">{sug.replace.row}</td>
            <td className="current-value">
              <span className="value-text">{sug.replace.original}</span>
            </td>
            <td className="suggested-value">
              <span className="value-text">{sug.replace.suggested_value}</span>
            </td>
            <td className="reference-row">{sug.replace.suggested_with_row}</td>
            <td className="similarity-score">
              <span className="similarity-badge">{(sug.replace.similarity * 100).toFixed(1)}%</span>
            </td>
            <td className="action-cell">
              <button onClick={() => handleAcceptSuggestion(sug.replace)} className="accept-button">
                ✓ Accept
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</div>

<div className="button-row">
          <div className="download-section">
  {downloadLink && (
    <a className="download-link primary" href={downloadLink} download>
      Download Clustered CSV
    </a>
  )}
</div>


          {/* Navigation Buttons */}
      <div style={{ marginTop: "2rem", display: "flex", justifyContent: "flex-end" }}>
  <button onClick={() => navigate('/cluster/supplier-name')}>
    Next → Supplier Name
  </button>
</div>
</div>

        </>
      )}
    </div>
  );
};


export default CosineClusterImporterName;
