import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './css/ClusterPage.css'; // reusing the same CSS
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function ClusterResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const { clusteredFilename, excelFilename, preview, clusterColumn } = location.state || {};

  if (!clusteredFilename || !excelFilename || !preview || preview.length === 0) {
    return <p>Missing clustering data. Please go back and try again.</p>;
  }

  const handleProceedToAnalysis = () => {
    navigate('/analysis-catalog', {
      state: {
        cleanedFilename: clusteredFilename,
        clusterColumn: clusterColumn
      }
    });
  };

  return (
    <div className="cluster-container">
      <div className="cluster-card">
        <h2>Clustering Results</h2>
        <p><b>Clustered Column:</b> {clusterColumn}</p>

        {/* Button Actions */}
        <div className="action-buttons">
          <a
            href={`${API_BASE_URL}/api/download/${clusteredFilename}`}
            className="download-btn"
            download
          >
            Download Clustered CSV
          </a>

          <a
            href={`${API_BASE_URL}/api/download/${excelFilename}`}
            className="excel-download-btn"
            download
          >
            Download Color-Coded Excel
          </a>

          <button
            onClick={() => navigate(-1)}
            className="excel-download-btn back-btn"
          >
            ← Go Back
          </button>

          <button
            onClick={handleProceedToAnalysis}
            className="excel-download-btn proceed-btn"
          >
            Proceed to Analysis →
          </button>
    
        </div>
        

        {/* Table */}
        <h3 className="preview-heading">Cluster Preview</h3>
        <div className="table-wrapper">
          <table className="preview-table">
            <thead>
              <tr>
                {Object.keys(preview[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.map((row, i) => (
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
  );
}
