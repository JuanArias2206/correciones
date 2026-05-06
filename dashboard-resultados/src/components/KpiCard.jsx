import React from 'react';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';

const COLOR_MAP = {
  primary:  { icon: 'rgba(129,140,248,0.12)', glow: 'rgba(129,140,248,0.22)' },
  success:  { icon: 'rgba(52,211,153,0.12)',  glow: 'rgba(52,211,153,0.22)'  },
  danger:   { icon: 'rgba(248,113,113,0.12)', glow: 'rgba(248,113,113,0.22)' },
  warning:  { icon: 'rgba(251,191,36,0.12)',  glow: 'rgba(251,191,36,0.22)'  },
  pink:     { icon: 'rgba(244,114,182,0.12)', glow: 'rgba(244,114,182,0.22)' },
  cyan:     { icon: 'rgba(34,211,238,0.12)',  glow: 'rgba(34,211,238,0.22)'  },
  violet:   { icon: 'rgba(167,139,250,0.12)', glow: 'rgba(167,139,250,0.22)' },
  orange:   { icon: 'rgba(251,146,60,0.12)',  glow: 'rgba(251,146,60,0.22)'  },
};

const parseNumeric = (value) => {
  if (typeof value === 'number') return value;
  const str = String(value).replace(/\./g, '').replace(/,/g, '');
  const n = parseFloat(str);
  return isNaN(n) ? null : n;
};

const KpiCard = ({ label, value, sub, icon, onClick, active, color = 'primary' }) => {
  const colors   = COLOR_MAP[color] || COLOR_MAP.primary;
  const numVal   = parseNumeric(value);
  const isNum    = numVal !== null && numVal > 99;
  const isLong   = !isNum && String(value).length > 18;

  return (
    <motion.div
      className={`kpi-card ${onClick ? 'kpi-clickable' : ''} ${active ? 'kpi-active' : ''}`}
      onClick={onClick}
      title={onClick ? 'Clic para filtrar el dashboard' : undefined}
      style={{ '--kpi-glow': colors.glow, '--kpi-icon-bg': colors.icon }}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileTap={onClick ? { scale: 0.97 } : {}}
    >
      <div className="kpi-top-row">
        <div style={{ flex: 1 }} />
        {icon && <div className="kpi-icon-wrap">{icon}</div>}
      </div>
      <div>
        <div className="kpi-label">{label}</div>
        <div className={`kpi-value${isLong ? ' kpi-text-sm' : ''}`} title={String(value)}>
          {isNum ? (
            <CountUp
              key={numVal}
              end={numVal}
              duration={1.6}
              separator="."
              decimal=","
              decimals={0}
              useEasing
            />
          ) : (
            value
          )}
        </div>
        {sub && <div className="kpi-sub">{sub}</div>}
      </div>
    </motion.div>
  );
};

export default KpiCard;
