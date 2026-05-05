import React from 'react';

const KpiCard = ({ label, value, sub }) => {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
};

export default KpiCard;
