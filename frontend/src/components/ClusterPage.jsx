import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import { useNavigate } from 'react-router-dom'; // ADD THIS

import './css/ClusterPage.css';

export default function ClusterPage() {
/*   const location = useLocation();
  const cleanedName = location.state?.cleanedFilename; */
  const cleanedName = sessionStorage.getItem("df_cleaned");

  const [column, setColumn] = useState('');
  const [columns, setColumns] = useState([]);
  const [preview, setPreview] = useState([]);
  const [clusteredFile, setClusteredFile] = useState('');
  const [status, setStatus] = useState('');
  const [excelReady, setExcelReady] = useState(false);
  const [excelFile, setExcelFile] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  const navigate = useNavigate(); // ADD THIS

  useEffect(() => {
    // Fetch headers of the cleaned file
    if (cleanedName) {
      axios
        .get(`http://localhost:5000/api/headers/${cleanedName}`)
        .then((res) => setColumns(res.data.headers))
        .catch(() => setColumns([]));
    }
  }, [cleanedName]);

const handleCluster = async () => {
  setStatus('Clustering in progress...');
  try {
    console.log("Clustering with column:", column);  // Add this for debugging
    console.log("Payload:", { column });
    console.log("Sending clustering request:", {
  column: column,
  filename: sessionStorage.getItem("df_cleaned"),
});

    const res = await axios.post('http://localhost:5000/api/cluster', {
      filename: cleanedName,
      column: column,
    });

    const preview = res.data.preview;
    const clustered_filename = res.data.clustered_filename;
    sessionStorage.setItem("df_clustered", clustered_filename);
   /*  await axios.post('http://localhost:5000/api/set-clustered-session', {
  filename: clustered_filename
}); */

     

    const excelRes = await axios.post('http://localhost:5000/api/export-colored-excel', {
      filename: clustered_filename,
      cluster_column: column,
      
    });

    const excel_filename = excelRes.data.excel_filename;
    navigate('/cluster-results', {
      state: {
        clusteredFilename: clustered_filename,
        excelFilename: excel_filename,
        preview: preview,
        clusterColumn: column,
      },
    });

  } catch (err) {
    console.error(' Clustering failed:', err);
    setStatus(' Clustering failed.');
  }
};


  return (
  <div className="cluster-container">
    <h2>Clustering</h2>
    <p>
      Clustering cleaned file: <b>{cleanedName}</b>
    </p>

    {/* FLEX SECTION START */}
    <div className="cluster-flex">
      {/* Left: Info Card */}
      <div className="info-card">
        <h3>What does this section do?</h3>
        <p>
          Cleans and groups similar product names to make the data more consistent and easier to work with.
        </p>

        {!showDetails ? (
          <button className="toggle-btn" onClick={() => setShowDetails(true)}>
            Learn more →
          </button>
        ) : (
          <>
            <ul className="info-details">
              <li>
                Many product names in raw data contain extra details, inconsistent formats, or small spelling differences.
              </li>
              <li>
                This section removes unnecessary text while keeping important product codes like <code>AR-740</code> or <code>PQ0015066</code>.
              </li>
              <li>
                It then identifies product names that are very similar and groups them under a common label.
              </li>
              <li>
                A new column is added to the data with these cleaned and grouped names.
              </li>
            </ul>
            <p className="why-it-matters">
              <strong>Why this matters:</strong><br />
              Without cleaning, similar products may be treated as different items. This step ensures cleaner data and more accurate analysis.
            </p>
            <button className="toggle-btn" onClick={() => setShowDetails(false)}>
              Show less ▲
            </button>
          </>
        )}
      </div>

      {/* Right: Clustering Controls */}
      <div className="cluster-controls">
        <select value={column} onChange={(e) => setColumn(e.target.value)}>
          <option value="">-- Select column to cluster on --</option>
          {columns.map((col) => (
            <option key={col} value={col}>
              {col}
            </option>
          ))}
        </select>

        <button disabled={!column} onClick={handleCluster}>
          Cluster Data
        </button>

        {status && <p className="status-message">{status}</p>}
      </div>
    </div>
    {/* FLEX SECTION END */}

    {/* Optional Preview Table */}
    {preview.length > 0 && (
      <>
        <h3>Clustered Preview</h3>
        <table className="preview-table">
          <thead>
            <tr>{Object.keys(preview[0]).map((k) => <th key={k}>{k}</th>)}</tr>
          </thead>
          <tbody>
            {preview.map((row, i) => (
              <tr key={i}>
                {Object.values(row).map((v, j) => (
                  <td key={j}>{v}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <a href={`http://localhost:5000/api/download/${clusteredFile}`} download>
          ⬇ Download Clustered CSV
        </a>
        {excelReady && (
          <div className="excel-notification">
            <p>Color-coded Excel is ready!</p>
            <a
              href={`http://localhost:5000/api/download/${excelFile}`}
              download
              className="excel-download-btn"
            >
              Download Color-Coded Excel
            </a>
          </div>
        )}
      </>
    )}
  </div>
);

}