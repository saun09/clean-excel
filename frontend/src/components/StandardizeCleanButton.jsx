import React, { useState } from 'react';
import axios from 'axios';
import './css/StandardizeCleanButton.css';
import { useNavigate } from 'react-router-dom';

const StandardizeCleanButton = ({ filename, onStatusUpdate, onCleanComplete }) => {
  const [cleanedData, setCleanedData] = useState([]);
  const [downloadLink, setDownloadLink] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const handleStandardize = async () => {
    setLoading(true);
    setError(null);
    onStatusUpdate?.('Cleaning started...');

    try {
      // 🟢 Send filename in POST body
      const response = await axios.post('http://localhost:5000/api/standardize', { filename }, {withCredentials: true});



      const cleanedFilename = response.data.cleaned_filename;

      // 🟢 Fetch cleaned file as text
      const csvResp = await axios.get(`http://localhost:5000/api/download/${cleanedFilename}`);

      const rows = csvResp.data.split('\n').map(line => line.split(','));
      const headers = rows[0];
      const dataRows = rows.slice(1).filter(row => row.length === headers.length);

      const cleanedDataJson = dataRows.map(row =>
        headers.reduce((obj, key, i) => {
          obj[key] = row[i];
          return obj;
        }, {})
      );

      setCleanedData(cleanedDataJson);
      setDownloadLink(`http://localhost:5000/api/download/${cleanedFilename}`);
      onStatusUpdate?.('Cleaning complete ✅');
      onCleanComplete?.(response.data.cleaned_filename);
      sessionStorage.setItem("df_cleaned", response.data.cleaned_filename);
      navigate('/cluster/item-description', { //changed 'cosine-similarity'
      state: { cleanedFilename }
     });

    } catch (err) {
      console.error('Standardization error:', err);
      setError('Failed to standardize and clean data.');
      onStatusUpdate?.('Cleaning failed ❌');
    }

    setLoading(false);
  };

  return (
    <div className="standardize-container">
      <button className="standardize-button" onClick={handleStandardize} disabled={loading}>
        {loading ? 'Cleaning...' : 'Proceed to standardization'}
      </button>

      {error && <div className="error-message">{error}</div>}

      {cleanedData.length > 0 && (
        <div className="cleaned-table-container">
          <h3>Cleaned Data Preview</h3>
          <table className="preview-table">
            <thead>
              <tr>
                {Object.keys(cleanedData[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cleanedData.slice(0, 10).map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => (
                    <td key={j}>{val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {downloadLink && (
            <a className="download-link" href={downloadLink} download>
              ⬇ Download Cleaned CSV
            </a>
          )}
        </div>
      )}
    </div>
  );
};


export default StandardizeCleanButton;
