import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, AlertCircle } from 'lucide-react';
import './css/FileUpload.css';
import csvIcon from '../assets/icons/csv.png';
import xlsxIcon from '../assets/icons/excel.png';
import tipIcon from '../assets/icons/tip.png';

const FileUpload = ({ onUpload }) => {
  const [file, setFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('idle');
  const [previewData, setPreviewData] = useState([]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.csv') || droppedFile.name.endsWith('.xlsx'))) {
      setFile(droppedFile);
      uploadFile(droppedFile);
    }
  }, []);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      uploadFile(selectedFile);
    }
  };

  const uploadFile = async (fileToUpload) => {
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const response = await axios.post('http://localhost:5000/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }, {withCredentials: true});

      console.log("Upload success:", response.data);
      console.log('Preview Data:', response.data.preview);
      setPreviewData(response.data.preview);
      setUploadStatus('success');

      sessionStorage.setItem("filename", response.data.filename);
      console.log("Saved filename to sessionStorage:", sessionStorage.getItem("filename"));

      onUpload(response.data.filename);
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h1>Upload Trade Data</h1>
        <p>Import your trade data files (.csv, .xlsx) to begin analysis</p>
      </div>

      <div className="upload-grid">
        {/* Left: File Upload */}
        <div className="file-upload">
          <div
            className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <UploadCloud className="upload-icon" />
            <p>Drop your files here<br /><small>or click to browse</small></p>
            <input
              type="file"
              className="file-input"
              onChange={handleFileSelect}
              accept=".csv,.xlsx"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="select-button">
              Browse Files
            </label>
          </div>

          {uploadStatus === 'uploading' && (
            <div className="status-message">Uploading...</div>
          )}
          {uploadStatus === 'success' && (
            <div className="status-message success">
              <CheckCircle className="inline-icon" />
              File uploaded successfully!
            </div>
          )}
          {uploadStatus === 'error' && (
            <div className="status-message error">
              <AlertCircle className="inline-icon" />
              Error uploading file. Please try again.
            </div>
          )}
        </div>

        {/* Right: Supported Formats */}
        <div className="upload-info">
          <h2>Supported Formats</h2>
          <p className="upload-subtext">We support the following file formats</p>

          <div className="format-card">
            <img src={csvIcon} alt="CSV Icon" className="format-icon" />
            <div>
              <strong>.CSV Files</strong>
              <div className="format-desc">Comma-separated values</div>
            </div>
          </div>

          <div className="format-card">
            <img src={xlsxIcon} alt="XLSX Icon" className="format-icon" />
            <div>
              <strong>.XLSX Files</strong>
              <div className="format-desc">Excel spreadsheets</div>
            </div>
          </div>

          <div className="format-card tip">
            <img src={tipIcon} alt="Tip Icon" className="format-icon" />
            <div>
              <strong>Tip:</strong> Ensure your data includes columns for product names, quantities, values, currencies, and country information for best results.
            </div>
          </div>
        </div>
      </div>

      {previewData && previewData.length > 0 && (
  <>
    {/* Data Preview Card */}
    <div className="preview-container">
      <h3>Data Preview</h3>
      <p className="upload-subtext">This is the raw preview of the uploaded file.</p>
      <table className="preview-table">
        <thead>
          <tr>
            {Object.keys(previewData[0]).map((key) => (
              <th key={key}>{key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {previewData.map((row, index) => (
            <tr key={index}>
              {Object.values(row).map((value, cellIndex) => (
                <td key={cellIndex}>
                  {value !== null && value !== undefined && !Number.isNaN(value)
                    ? String(value)
                    : '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>


  </>
)}

    </div>
  );
};

export default FileUpload;
