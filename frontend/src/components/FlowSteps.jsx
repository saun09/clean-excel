import React from 'react';
import './css/FlowStep.css';
import { FaUpload } from 'react-icons/fa';
import { FiLayers, FiBarChart2, FiAlertCircle } from 'react-icons/fi';
import { Link } from 'react-router-dom';

const steps = [
  {
    icon: <FaUpload />,
    title: 'Upload Data',
    subtitle: 'Import your trade data files',
    link: '/', // or '/file-upload' if you have one
  },
  {
    icon: <FiLayers />,
    title: 'Cluster',
    subtitle: 'Organize and group your data',
    link: '/cluster/item-description',
  },
  {
    icon: <FiBarChart2 />,
    title: 'Choose Analysis',
    subtitle: 'Select analysis methods',
    link: '/analysis-catalog',
  },
 /*  {
    icon: <FiAlertCircle />,
    title: 'Get Insights',
    subtitle: 'Discover actionable insights',
    link: '/analytics/company-analysis',
  }, */
];

const FlowSteps = () => {
  return (
    <div className="flow-steps">
      {steps.map((step, index) => (
        <React.Fragment key={index}>
          <Link to={step.link} className="step-link">
            <div className="step">
              <div className="icon">{step.icon}</div>
              <h3>{step.title}</h3>
              <p>{step.subtitle}</p>
            </div>
          </Link>
          {index < steps.length - 1 && <div className="arrow">→</div>}
        </React.Fragment>
      ))}
    </div>
  );
};

export default FlowSteps;
