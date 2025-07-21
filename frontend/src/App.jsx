// src/App.jsx
import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import FileUpload from './components/FileUpload';
import StandardizeCleanButton from './components/StandardizeCleanButton';
import ClusterPage from './components/ClusterPage';
import MainLayout from './components/MainLayout';
import ClusterResults from './components/ClusterResults';
import AnalysisCatalogPage from './components/AnalysisCatalogPage';
import FilterPage from './components/FilterPage';
import ForecastPage from './components/ForecastPage';

//import FuzzyStandardizer from '../../might not need/FuzzyStandardizer';
import CosineSimilarity  from './components/CosineSimilarity';

import CosineClusterItemDescription from './components/CosineClusterItemDescription';
import CosineClusterImporterName from './components/CosineClusterImporterName';
import CosineClusterSupplierName from './components/CosineClusterSupplierName';
import CompanyAnalysis from './components/CompanyAnalysis';
import ClusterAnalysisPage from './components/ClusterAnalysisPage';
import './App.css';
import ComparativeAnalysis from './components/ComparativeAnalysis';

function Home() {
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />

        {/* <Route path="/cluster" element={
          <MainLayout>
            <ClusterPage />
          </MainLayout>
        } /> */}
         <Route path="standardize-btn" element={
          <MainLayout>
            <StandardizeCleanButton />
          </MainLayout>
        } />

        <Route path="cosine-similarity" element={
          <MainLayout>
            <CosineSimilarity />
          </MainLayout>
        } />

          <Route path="/analysis-catalog" element={
          <MainLayout>
            <AnalysisCatalogPage />
          </MainLayout>
        } />
 

        <Route path="/cluster-results" element={
          <MainLayout>
            <ClusterResults />
          </MainLayout>
        } />

      

        <Route path="/analytics/filter" element={
          <MainLayout>
            <FilterPage />
          </MainLayout>
        } />

        <Route path="/analytics/forecast" element={
          <MainLayout>
            <ForecastPage />
          </MainLayout>
        } />

        <Route path="/analytics/comparative-analysis" element={
          <MainLayout>
            <ComparativeAnalysis />
          </MainLayout>
        } />

        <Route path="/analytics/company-analysis" element={
          <MainLayout>
            <CompanyAnalysis />
          </MainLayout>
        } />

        <Route path="/analytics/cluster-summary" element={
          <MainLayout>
            <ClusterAnalysisPage />
          </MainLayout>
        } />

         <Route path="/cluster/item-description" element={<CosineClusterItemDescription />} />
        <Route path="/cluster/importer-name" element={<CosineClusterImporterName />} />
        <Route path="/cluster/supplier-name" element={<CosineClusterSupplierName />} />

       {/*  <Route path="/analytics/fuzzy-standardize" element={
          <MainLayout>
            <FuzzyStandardizer />
          </MainLayout>
        } /> */}

        
      </Routes>
    </BrowserRouter>
  );
}
