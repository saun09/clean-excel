// src/components/MainLayout.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import './css/MainLayout.css'; // Adjusted path based on your structure

const MainLayout = ({ children }) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/logout`, {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        console.log("[DEBUG] Logout successful");
        navigate("/login");
      } else {
        console.log("[DEBUG] Logout failed");
        alert("Logout failed");
      }
    } catch (err) {
      console.error("[DEBUG] Logout error:", err);
    }
  };

  return (
    <div className="main-layout">
      <Sidebar />
      <div className="content-area">
        <div className="top-bar">
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

export default MainLayout;
