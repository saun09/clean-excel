import React, { useState } from 'react';
import axios from 'axios';
import './css/CosineSimilarity.css';
import { useLocation } from 'react-router-dom';

import { useNavigate } from 'react-router-dom'; // ✅ REQUIRED for navigation

const CosineClusterSupplierName = () => {
  const location = useLocation();
  const cleanedFilename = location.state?.cleanedFilename || sessionStorage.getItem("df_cleaned");
  const selectedColumn = "Supplier_Name";

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
      if (response.data.final_filename) {
  sessionStorage.setItem("finalClusteredFilename", response.data.final_filename);
}

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

 /*  const handleProceedToAnalysis = () => {
  sessionStorage.setItem("clusterColumn", selectedColumn); // ✅ Save for FilterPage too
  navigate('/analysis-catalog');
};
 */
  const handleProceedToAnalysis = () => {
    navigate('/analysis-catalog', {
      state: {
        cleanedFilename: cleanedFilename,
        clusterColumn: selectedColumn
      }
    });
  };


  return (
    <div className="cosine-similarity-container">
      <h2>Cluster: Supplier Name</h2>
      <p>Clustering using Cosine Similarity on the <b>Supplier Name</b> column.</p>

      <div className="clustering-controls">
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

        <button onClick={handleRunClustering} disabled={loading}>
          {loading ? "Clustering..." : "Run Clustering"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {clusteredData.length > 0 && (
        <>
          <h3>Clustered Preview</h3>
          <table className="preview-table">
            <thead>
              <tr>
                {Object.keys(clusteredData[0]).map((key) => <th key={key}>{key}</th>)}
              </tr>
            </thead>
            <tbody>
              {clusteredData.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => <td key={j}>{val}</td>)}
                </tr>
              ))}
            </tbody>
          </table>

          {suggestions.length > 0 && (
            <div className="suggestions">
              <h3>Suggested Replacements</h3>
              {suggestions.map((sug, index) => (
                <div key={index}>
                  Replace Row {sug.replace.row} ("{sug.replace.original}") with Row {sug.replace.suggested_with_row} ("{sug.replace.suggested_value}") – Similarity: {(sug.replace.similarity * 100).toFixed(1)}%
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
          {/* Navigation Button */}
      <div style={{ marginTop: "2rem", display: "flex", justifyContent: "flex-start" }}>
        <button onClick={() => navigate('/cluster/importer-name')}>
          ← Back to Importer Name
        </button>
      </div>

      <div style={{ marginTop: "2rem", display: "flex", justifyContent: "center" }}>
  <button className="proceed-button" onClick={handleProceedToAnalysis}>
    Proceed to Analysis →
  </button>
</div>

        </>
      )}


    </div>
  );
};

export default CosineClusterSupplierName;
