// src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import FileUpload from './components/FileUpload';
import StandardizeCleanButton from './components/StandardizeCleanButton';
import ClusterPage from './components/ClusterPage';
import MainLayout from './components/MainLayout';
import ClusterResults from './components/ClusterResults';
import AnalysisCatalogPage from './components/AnalysisCatalogPage';
import FilterPage from './components/FilterPage';
import ForecastPage from './components/ForecastPage';
import CosineSimilarity from './components/CosineSimilarity';
import CosineClusterItemDescription from './components/CosineClusterItemDescription';
import CosineClusterImporterName from './components/CosineClusterImporterName';
import CosineClusterSupplierName from './components/CosineClusterSupplierName';
import CompanyAnalysis from './components/CompanyAnalysis';
import ClusterAnalysisPage from './components/ClusterAnalysisPage';
import ComparativeAnalysis from './components/ComparativeAnalysis';
import FlowSteps from './components/FlowSteps';

import Login from './components/Login';
import './App.css';

function Home({ authenticated }) {
  const [uploadedFileName, setUploadedFileName] = useState(null);
  const [cleaningStatus, setCleaningStatus] = useState(null);
  const navigate = useNavigate();

  const handleFileUpload = (filename) => {
    setUploadedFileName(filename);
    setCleaningStatus(null);
  };

  const handleCleanComplete = (cleanedFilename) => {
    navigate('/cluster', { state: { cleanedFilename } });
  };

  if (!authenticated) return <Navigate to="/login" replace />;

  return (
    <MainLayout>
      <FileUpload onUpload={handleFileUpload} />
      {uploadedFileName && (
        <>
          {cleaningStatus && <p className="status-message">{cleaningStatus}</p>}
          <StandardizeCleanButton
            filename={uploadedFileName}
            onStatusUpdate={setCleaningStatus}
            onCleanComplete={handleCleanComplete}
          />
        </>
      )}
    </MainLayout>
  );
}

function PrivateRoute({ authenticated, children }) {
  return authenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/check-auth', {
          method: 'GET',
          credentials: 'include',
        });
        if (res.ok) {
          console.log('[DEBUG] Authenticated session found');
          setAuthenticated(true);
        } else {
          console.log('[DEBUG] No active session');
        }
      } catch (err) {
        console.error('[DEBUG] Auth check failed:', err);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) return <p>Loading...</p>;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login setAuthenticated={setAuthenticated} />} />

        <Route
          path="/"
          element={
            <PrivateRoute authenticated={authenticated}>
              <Home authenticated={authenticated} />
            </PrivateRoute>
          }
        />

        <Route
          path="/file_upload"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><FileUpload /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/flow-steps"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><FlowSteps /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/standardize-btn"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><StandardizeCleanButton /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/cosine-similarity"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><CosineSimilarity /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/analysis-catalog"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><AnalysisCatalogPage /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/cluster-results"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><ClusterResults /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/analytics/filter"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><FilterPage /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/analytics/forecast"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><ForecastPage /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/analytics/company-analysis"
          element={
            <PrivateRoute authenticated={authenticated}>
              <MainLayout><CompanyAnalysis /></MainLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/cluster/item-description"
          element={
            <PrivateRoute authenticated={authenticated}>
              <CosineClusterItemDescription />
            </PrivateRoute>
          }
        />
        <Route
          path="/cluster/importer-name"
          element={
            <PrivateRoute authenticated={authenticated}>
              <CosineClusterImporterName />
            </PrivateRoute>
          }
        />
        <Route
          path="/cluster/supplier-name"
          element={
            <PrivateRoute authenticated={authenticated}>
              <CosineClusterSupplierName />
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
