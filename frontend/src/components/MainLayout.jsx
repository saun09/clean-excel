// src/components/MainLayout.jsx
import React from 'react';
import Sidebar from './Sidebar';
import './css/MainLayout.css'; // Adjusted path based on your structure

const MainLayout = ({ children }) => {
  return (
    <div className="main-layout">
      <Sidebar />
      <div className="content-area">
        {children}
      </div>
    </div>
  );
};

export default MainLayout;
