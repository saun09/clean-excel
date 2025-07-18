/* import React, {useState} from 'react';
import axios from 'axios';
import './css/CosineSimilarity.css';
import { useLocation } from 'react-router-dom';
console.log("CosineSimilarity rendered");

const CosineSimilarity = () => {
    const location = useLocation();
    const cleanedFilename = location.state?.cleanedFilename || sessionStorage.getItem("df_cleaned");

    const [selectedColumn, setSelectedColumn] = useState('');
    const [threshold, setThreshold] = useState(0.8);
    const [clusteredData, setClusteredData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const[downloadLink, setDownloadLink] = useState(null);
    const [excelDownloadLink, setExcelDownloadLink] = useState(null);
    const [suggestions, setSuggestions] = useState([]);


    const handleRunClustering = async() => {
        if(!selectedColumn) {
            setError("Please select a column to cluster.");
            return;
        }

        setLoading(true);
        setError('');
        setClusteredData([]);
        setSuggestions([]);
        setSuggestions([]);
        console.log("Suggestions cleared before clustering");


        try{
          
            console.log("Running clustering with column:", selectedColumn, "and threshold:", threshold);
            const response = await axios.post('http://localhost:5000/api/cosine_cluster', {
                filename: cleanedFilename,
                column: selectedColumn,
                threshold : threshold,
            }, {withCredentials: true});

            console.log('Clustering successful:', response.data);
            setClusteredData(response.data.clustered_preview || []);
            setDownloadLink(`http://localhost:5000/api/download/${response.data.output_file}`);
            setDownloadLink(`http://localhost:5000/api/download/${response.data.output_file}`);
            setExcelDownloadLink(`http://localhost:5000/api/download/${response.data.excel_file}`);
            setSuggestions(response.data.replacement_suggestions || []);
            console.log("📌 Suggestions from backend:", response.data.replacement_suggestions);
            response.data.replacement_suggestions.forEach((s, i) =>
              console.log(`➡ Row ${s.replace.row} <- Row ${s.replace.suggested_with_row} [${s.replace.similarity}]`)
            );


        }catch(err){
            console.error('Clustering error:', err);
            setError('Failed to run clustering. Please try again.');
        }
        setLoading(false);
    };

    if (!cleanedFilename) {
  return <div className="cosine-similarity-container">⚠️ No cleaned file found. Please upload and clean a file first.</div>;
}

  const handleAcceptSuggestion = async (suggestion) => {
  try {
    const response = await axios.post('http://localhost:5000/api/apply_replacement', {
      filename: cleanedFilename,
      column: selectedColumn,
      targetRow: suggestion.row,
      newValue: suggestion.suggested_value
    }, { withCredentials: true });

    console.log("Replacement applied", response.data);
    handleRunClustering(); // Refresh after applying
  } catch (err) {
    console.error('Error applying suggestion:', err);
    setError("Failed to apply suggestion.");
  }
};

  return (
    <div className="cosine-similarity-container">
      <h2>Cosine Similarity Clustering</h2>
      <p>Apply clustering on a specific text column using TF-IDF + Cosine Similarity.</p>

      <div className="clustering-controls">
        <label>
          Select column:
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
          >
            <option value="">--Choose Column--</option>
            <option value="Item_Description">Item_Description</option>
            <option value="Importer_Name">Importer_Name</option>
            <option value="Supplier_Name">Supplier_Name</option>
          </select>
        </label>

        <label>
          Similarity Threshold:
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
          />
        </label>

        <button onClick={handleRunClustering} disabled={loading || !cleanedFilename}>
          {loading ? 'Clustering...' : 'Run Cosine Clustering'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {clusteredData.length > 0 && (
        <div className="clustered-preview">
          <h3>Clustered Data Preview</h3>
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

          {suggestions.length > 0 && (
  <div className="suggestions">
    <h3>Suggested Replacements</h3>
    {suggestions.map((sug, index) => (
      <div key={`${sug.replace.row}-${sug.replace.suggested_with_row}`} className="suggestion-box">

        Replace Row {sug.replace.row} ("{sug.replace.original}") 
        with Row {sug.replace.suggested_with_row} ("{sug.replace.suggested_value}") 
        – Similarity: {sug.replace.similarity}
        <button onClick={() => handleAcceptSuggestion(sug.replace)}>Accept</button>
      </div>
    ))}
  </div>
)}


          {downloadLink && (
            <a className="download-link" href={downloadLink} download>
              ⬇ Download Clustered CSV
            </a>
          )}
          {excelDownloadLink && (
            <a className="download-link" href={excelDownloadLink} download>
              🟨 Download Color-Coded Excel
            </a>
)}
        </div>
      )}
    </div>
  );
};

export default CosineSimilarity; */


import React, { useState } from 'react';
import axios from 'axios';
import './css/CosineSimilarity.css';
import { useLocation } from 'react-router-dom';

const CosineSimilarity = () => {
  const location = useLocation();
  const cleanedFilename = location.state?.cleanedFilename || sessionStorage.getItem("df_cleaned");

  const [selectedColumn, setSelectedColumn] = useState('');
  const [threshold, setThreshold] = useState(0.8);
  const [clusteredData, setClusteredData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadLink, setDownloadLink] = useState(null);
  const [excelDownloadLink, setExcelDownloadLink] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  /* const handleClusterAllColumns = async () => {
  setLoading(true);
  setError('');
  setClusteredData([]);
  setSuggestions([]);

  try {
    const response = await axios.post('http://localhost:5000/api/cosine_cluster_all', {
      filename: cleanedFilename,
      threshold: threshold
    }, { withCredentials: true });

    setClusteredData(response.data.clustered_preview || []);
    setDownloadLink(`http://localhost:5000/api/download/${response.data.output_file}`);
    setExcelDownloadLink(`http://localhost:5000/api/download/${response.data.excel_file}`);
    setSuggestions(response.data.replacement_suggestions || []);
  } catch (err) {
    console.error('Multi-column clustering failed:', err);
    setError("Failed to cluster all columns.");
  }
  setLoading(false);
}; */

  const handleRunClustering = async () => {
    if (!selectedColumn) {
      setError("Please select a column to cluster.");
      return;
    }

    setLoading(true);
    setError('');
    setClusteredData([]);
    setSuggestions([]);

    try {
      console.log("Running clustering with column:", selectedColumn, "and threshold:", threshold);
      const response = await axios.post('http://localhost:5000/api/cosine_cluster', {
        filename: cleanedFilename,
        column: selectedColumn,
        threshold: threshold,
      }, { withCredentials: true });

      console.log('Clustering successful:', response.data);
      setClusteredData(response.data.clustered_preview || []);
      setDownloadLink(`http://localhost:5000/api/download/${response.data.output_file}`);
      setExcelDownloadLink(`http://localhost:5000/api/download/${response.data.excel_file}`);
      setSuggestions(response.data.replacement_suggestions || []);
      console.log("Suggestions from backend:", response.data.replacement_suggestions);
    } catch (err) {
      console.error('Clustering error:', err);
      setError('Failed to run clustering. Please try again.');
    }
    setLoading(false);
  };

  const handleAcceptSuggestion = async (suggestion) => {
    try {
      const response = await axios.post('http://localhost:5000/api/apply_replacement', {
        filename: cleanedFilename,
        column: selectedColumn,
        targetRow: suggestion.row,
        newValue: suggestion.suggested_value
      }, { withCredentials: true });

      console.log("Replacement applied", response.data);
      handleRunClustering(); // Refresh after applying
    } catch (err) {
      console.error('Error applying suggestion:', err);
      setError("Failed to apply suggestion.");
    }
  };

  if (!cleanedFilename) {
    return (
      <div className="cosine-similarity-container">
        <div className="warning-message">
          No cleaned file found. Please upload and clean a file first.
        </div>
      </div>
    );
  }

  return (
    <div className="cosine-similarity-container">
      <div className="header-section">
        <h2>Cosine Similarity Clustering</h2>
        <p>Apply advanced clustering on text columns using TF-IDF + Cosine Similarity to find similar entries.</p>
      </div>

      <div className="clustering-controls">
        <div className="control-group">
          <label className="control-label">
            Select Column
          </label>
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            className="control-select"
          >
            <option value="">--Choose Column--</option>
            <option value="Item_Description">Item Description</option>
            <option value="Importer_Name">Importer Name</option>
            <option value="Supplier_Name">Supplier Name</option>
          </select>
        </div>

        <div className="control-group">
          <label className="control-label">
            Similarity Threshold
          </label>
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

        <button 
          onClick={handleRunClustering} 
          disabled={loading || !cleanedFilename}
          className="run-button"
        >
          {loading ? (
            <span className="loading-text">
              <span className="spinner"></span>
              Clustering...
            </span>
          ) : (
            'Run Cosine Clustering'
          )}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">❌</span>
          {error}
        </div>
      )}

      {clusteredData.length > 0 && (
        <div className="results-section">
          <div className="clustered-preview">
            <h3>Clustered Data Preview</h3>
            <div className="table-container">
              <table className="preview-table">
                <thead>
                  <tr>
                    {Object.keys(clusteredData[0]).map((key) => (
                      <th key={key}>{key.replace(/_/g, ' ')}</th>
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
                          <button 
                            onClick={() => handleAcceptSuggestion(sug.replace)}
                            className="accept-button"
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

          <div className="download-section">
            {downloadLink && (
              <a className="download-link primary" href={downloadLink} download>
                Download Clustered CSV
              </a>
            )}
           {/*  {excelDownloadLink && (
              <a className="download-link secondary" href={excelDownloadLink} download>
                Download Color-Coded Excel
              </a>
            )} */}
          </div>
        </div>
      )}
    </div>
  );
};

export default CosineSimilarity;