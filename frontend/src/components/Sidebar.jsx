import React from 'react';
import { Upload, ListTree, BarChart2, LogOut } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import logo from '../assets/AGRLogo.jpeg';
import './css/Sidebar.css';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    {
      label: 'Upload Data and Standardize',
      icon: <Upload size={18} />,
      to: '/',
    },
    {
      label: 'Cosine Clustering',
      icon: <ListTree size={18} />,
      to: '/cluster/item-description',
    },
    {
      label: 'Analysis Catalog',
      icon: <BarChart2 size={18} />,
      to: '/analysis-catalog',
    },
  ];

  const handleLogout = async () => {
    try {
      const res = await fetch("${API_BASE_URL}/api/logout", {
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
    <div className="sidebar">
      <div className="sidebar-logo">
        <img src={logo} alt="AGR Logo" className="logo-img" />
        <div className="product-name">Xelly</div>
      </div>
      <nav className="nav-links">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`nav-item ${location.pathname === item.to ? 'active' : ''}`}
          >
            {item.icon}
            <span>{item.label}</span>
          </Link>
        ))}
        <button className="nav-item logout-button" onClick={handleLogout}>
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </nav>
    </div>
  );
};

export default Sidebar;
