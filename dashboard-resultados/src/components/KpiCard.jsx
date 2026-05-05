import React from 'react';

const KpiCard = ({ label, value, sub, icon, onClick, active }) => {
  return (
    <div
      className={`kpi-card anim-up ${onClick ? 'kpi-clickable' : ''} ${active ? 'kpi-active' : ''}`}
      onClick={onClick}
      title={onClick ? 'Clic para filtrar el dashboard por este valor' : undefined}
    >
      {icon && <div className="kpi-icon">{icon}</div>}
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" title={String(value)}>{value}</div>
      {sub && <div className="kpi-sub" title={String(sub)}>{sub}</div>}
    </div>
  );
};

export default KpiCard;
