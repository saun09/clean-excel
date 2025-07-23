import React from 'react';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const DataTable = ({ data, columns }) => {
  if (!data || data.length === 0) return <p>No data available</p>;

  return (
    <div className="data-table">
      <table>
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.Header}>{col.Header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {columns.map(col => (
                <td key={`${i}-${col.accessor}`}>
                  {typeof row[col.accessor] === 'number' 
                    ? row[col.accessor].toLocaleString() 
                    : row[col.accessor]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;