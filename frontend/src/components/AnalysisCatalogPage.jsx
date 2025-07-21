import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Filter,
  LineChart,
  BarChart3,
  Building2,
  HelpCircle,
  FolderKanban,
  Award,
  ScatterChart,
  LayoutGrid
} from 'lucide-react';
import './css/AnalysisCatalog.css';


export default function AnalysisCatalogPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { cleanedFilename, clusterColumn } = location.state || {};

  const handleNavigate = (route) => {
    navigate(route, {
      state: {
        cleanedFilename,
        clusterColumn,
      },
    });
  };

 /*  if (!cleanedFilename || !clusterColumn) {
    return <p>Missing file or cluster data. Please complete clustering step first.</p>;
  } */

  const cards = [
    {
      title: 'Filter & Analyze Trade Data',
      description: 'Drill down by Trade Type, Importer, and Supplier.',
      icon: <Filter size={28} />,
      route: '/analytics/filter',
    },
    {
      title: 'Forecast Product Price or Quantity',
      description: 'Predict future values using time series models.',
      icon: <LineChart size={28} />,
      route: '/analytics/forecast',
    },
    {
      title: 'Comparative Quantity Analysis',
      description: 'Compare quarters, months or years for products.',
      icon: <BarChart3 size={28} />,
      route: '/analytics/comparative-analysis', // Updated route to match new structure
    },
    {
      title: 'Analysis Company Wise',
      description: 'Break down key metrics by company.',
      icon: <Building2 size={28} />,
      route: '/analytics/company-analysis',
    },
    /* {
      title: 'Business Questions',
      description: 'Answer strategic trade queries using your data.',
      icon: <HelpCircle size={28} />,
      route: '/business-questions',
    }, */
    {
      title: 'Cluster Summary',
      description: 'Get cluster-level record counts, sums, averages.',
      icon: <FolderKanban size={28} />,
      route: '/analytics/cluster-summary',
    },
    /* {
      title: 'Top Clusters',
      description: 'Rank clusters by volume, value or quantity.',
      icon: <Award size={28} />,
      route: '/top-clusters',
    }, */
 /*    {
  title: 'Cross-Analysis',
  description: 'Compare clusters against categories like type, country.',
  icon: <ScatterChart size={28} />,
  route: '/cross-analysis',
}, */
/* {
  title: 'Detailed Breakdown',
  description: 'Category-wise breakdowns for each cluster.',
  icon: <LayoutGrid size={28} />,
  route: '/detailed-breakdown',
} */

  ];

  return (
    <div className="analysis-catalog-container">
      <h2>Select Type of Analysis</h2>
      <p style={{ fontSize: '0.95rem', marginBottom: '1rem' }}>
        You can now perform deeper insights using your clustered trade data.
      </p>

      <div className="analysis-options-grid">
        {cards.map((card, index) => (
          <div
            key={index}
            className="analysis-card"
            onClick={() => handleNavigate(card.route)}
          >
            <div className="card-icon">{card.icon}</div>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
