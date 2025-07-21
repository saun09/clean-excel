import React from 'react';
import { Home, Upload, Sliders, ListTree, BarChart2, Share2 } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import logo from '../assets/AGRLogo.jpeg';
import './css/Sidebar.css';

const Sidebar = () => {
  const location = useLocation();

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
      </nav>
    </div>
  );
};

export default Sidebar;
