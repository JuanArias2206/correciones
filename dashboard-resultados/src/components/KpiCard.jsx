import React from 'react';

const KpiCard = ({ label, value, sub, icon }) => {
  return (
    <div className="kpi-card anim-up">
      {icon && <div className="kpi-icon">{icon}</div>}
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" title={String(value)}>{value}</div>
      {sub && <div className="kpi-sub" title={String(sub)}>{sub}</div>}
    </div>
  );
};

export default KpiCard;
