import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, Sector,
} from 'recharts';
import KpiCard from './components/KpiCard';
import DataTable from './components/DataTable';
import ChatBot from './components/ChatBot';
import ThemeToggle from './components/ThemeToggle';
import {
  kpis as baseKpis, sustancias as baseSustancias, intencionalidad as baseIntenc,
  sexo as baseSexo, sustanciasPorIntencionalidad as baseSustInt,
  sustanciaSexo as baseSustSexo, productosTodos, conteoCategorias as baseConteoCat,
  resultadosLlm, resumenCategorias, baseCompleta, metadata
} from './data/data';

/* ─── ANIMATION VARIANTS ────────────────────────────────────────── */
const secVar = {
  hidden:  { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22,1,0.36,1] } }
};
const gridVar = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.065 } }
};
const cardVar = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.42, ease: [0.22,1,0.36,1] } }
};

/* ─── NAV SECTIONS ───────────────────────────────────────────────── */
const sections = [
  { id: 'kpis',           label: 'KPIs',            icon: '\u{1F4CA}' },
  { id: 'sustancias',     label: 'Sustancias',       icon: '\u{1F9EA}' },
  { id: 'sexo',           label: 'Por Sexo',         icon: '\u26A5'    },
  { id: 'intencionalidad',label: 'Intencionalidad',  icon: '\u{1F3AF}' },
  { id: 'productos',      label: 'Productos',        icon: '\u{1F4E6}' },
  { id: 'tabla',          label: 'Tabla',            icon: '\u{1F50D}' },
  { id: 'hallazgos',      label: 'Hallazgos',        icon: '\u{1F4A1}' },
  { id: 'originales',     label: 'Graficas',         icon: '\u{1F5BC}' },
];

/* ─── CHART GRADIENTS (injected once as SVG defs) ─────────────────── */
const GradDefs = () => (
  <svg width="0" height="0" style={{ position: 'absolute', overflow: 'hidden' }}>
    <defs>
      <linearGradient id="gPrimary" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stopColor="#4f46e5" />
        <stop offset="100%" stopColor="#818cf8" />
      </linearGradient>
      <linearGradient id="gCyan" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stopColor="#0891b2" />
        <stop offset="100%" stopColor="#22d3ee" />
      </linearGradient>
      <linearGradient id="gPink" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stopColor="#db2777" />
        <stop offset="100%" stopColor="#f472b6" />
      </linearGradient>
      <linearGradient id="gDanger" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stopColor="#dc2626" />
        <stop offset="100%" stopColor="#f87171" />
      </linearGradient>
      <linearGradient id="gSuccess" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stopColor="#059669" />
        <stop offset="100%" stopColor="#34d399" />
      </linearGradient>
    </defs>
  </svg>
);

/* ─── CUSTOM DARK TOOLTIP ────────────────────────────────────────── */
const DarkTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div className="custom-tooltip-label">{label}</div>
      {payload.map((entry, i) => (
        <div className="custom-tooltip-row" key={i}>
          <span className="custom-tooltip-dot" style={{ background: entry.color }} />
          <span className="custom-tooltip-name">{entry.name}</span>
          <span className="custom-tooltip-val">{Number(entry.value).toLocaleString('es-CO')}</span>
        </div>
      ))}
    </div>
  );
};

/* ─── ACTIVE DONUT SHAPE ─────────────────────────────────────────── */
const ActiveDonutShape = (props) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, value, percent } = props;
  return (
    <g>
      <text x={cx} y={cy - 10} textAnchor="middle" fill="#f1f5f9" fontSize={22} fontWeight={900} fontFamily="Inter">
        {Number(value).toLocaleString('es-CO')}
      </text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill="#64748b" fontSize={10} fontWeight={500}>
        {payload.name}
      </text>
      <text x={cx} y={cy + 28} textAnchor="middle" fill="#818cf8" fontSize={13} fontWeight={700}>
        {(percent * 100).toFixed(1)}%
      </text>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 7} startAngle={startAngle} endAngle={endAngle} fill={fill} />
      <Sector cx={cx} cy={cy} innerRadius={outerRadius + 10} outerRadius={outerRadius + 14} startAngle={startAngle} endAngle={endAngle} fill={fill} opacity={0.45} />
    </g>
  );
};

/* ─── SECTION HEADER ─────────────────────────────────────────────── */
const SH = ({ icon, title, badge }) => (
  <div className="section-header">
    <div className="section-title">
      <span className="section-title-icon">{icon}</span>
      {title}
      {badge && <span className="card-badge">{badge}</span>}
    </div>
    <div className="section-divider" />
  </div>
);

/* ═══════════════════════════════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════════════════════════════ */
const App = () => {
  const [theme,          setTheme]          = useState(() => localStorage.getItem('theme') || 'dark');
  const [sidebarOpen,    setSidebarOpen]    = useState(false);
  const [activeSection,  setActiveSection]  = useState('kpis');
  const [filtros,        setFiltros]        = useState({ sexo: null, sustancia: null, intencionalidad: null, topN: 'todas' });
  const [pieSexoIdx,     setPieSexoIdx]     = useState(0);
  const [pieIntencIdx,   setPieIntencIdx]   = useState(0);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => setTheme(p => p === 'dark' ? 'light' : 'dark'), []);

  const setFilter = useCallback((key, val) =>
    setFiltros(p => p[key] === val ? { ...p, [key]: null } : { ...p, [key]: val }), []);
  const clearAll  = useCallback(() =>
    setFiltros({ sexo: null, sustancia: null, intencionalidad: null, topN: 'todas' }), []);
  const clearOne  = useCallback((key) =>
    setFiltros(p => ({ ...p, [key]: null })), []);

  /* ── Filtered base ── */
  const filteredBase = useMemo(() => {
    let d = baseCompleta;
    if (filtros.sexo)            d = d.filter(r => r.sexo === filtros.sexo);
    if (filtros.sustancia)       d = d.filter(r => String(r.grupos_sustancia_final) === filtros.sustancia);
    if (filtros.intencionalidad) d = d.filter(r => r.intencionalidad === filtros.intencionalidad);
    return d;
  }, [filtros.sexo, filtros.sustancia, filtros.intencionalidad]);

  /* ── KPIs ── */
  const kpis = useMemo(() => {
    const total = filteredBase.length;
    const int   = filteredBase.filter(r => r.intencionalidad === 'intencional').length;
    const noint = filteredBase.filter(r => r.intencionalidad === 'no_intencional').length;
    const sexoF = filteredBase.filter(r => r.sexo === 'F').length;
    const sexoM = filteredBase.filter(r => r.sexo === 'M').length;
    const sm = {};
    filteredBase.forEach(r => { const s = r.grupos_sustancia_final; if (!s || s==='nan') return; sm[s]=(sm[s]||0)+1; });
    const sa = Object.entries(sm).map(([s,n])=>({sustancia:s,numero_registros:n})).sort((a,b)=>b.numero_registros-a.numero_registros);
    return {
      total_registros: total, intencional: int, no_intencional: noint,
      pct_intencional:    total ? ((int/total)*100).toFixed(1)   : 0,
      pct_no_intencional: total ? ((noint/total)*100).toFixed(1) : 0,
      sexo_f: sexoF, sexo_m: sexoM,
      sustancia_mas_frecuente: sa[0]?.sustancia||'-',
      segunda_sustancia:       sa[1]?.sustancia||'-',
      tercera_sustancia:       sa[2]?.sustancia||'-',
      categorias_detectadas:   sa.length,
    };
  }, [filteredBase]);

  const sustancias = useMemo(() => {
    const m = {};
    filteredBase.forEach(r => { const s=r.grupos_sustancia_final; if(!s||s==='nan') return; m[s]=(m[s]||0)+1; });
    return Object.entries(m).map(([k,v])=>({sustancia:k,numero_registros:v})).sort((a,b)=>b.numero_registros-a.numero_registros);
  }, [filteredBase]);

  const sustanciaMasIntencional = useMemo(() => {
    const m = {};
    filteredBase.forEach(r => {
      const s=r.grupos_sustancia_final; if(!s||s==='nan') return;
      if(!m[s]) m[s]={total:0,intencional:0};
      m[s].total++;
      if(r.intencionalidad==='intencional') m[s].intencional++;
    });
    let best=null;
    Object.entries(m).forEach(([s,d]) => {
      if(d.total<10) return;
      const pct=d.intencional/d.total;
      if(!best||pct>best.pct) best={sustancia:s,pct};
    });
    return best?.sustancia||'-';
  }, [filteredBase]);

  const sexoData = useMemo(() => {
    const m = {};
    filteredBase.forEach(r => {
      const s=r.grupos_sustancia_final; if(!s||s==='nan') return;
      if(!m[s]) m[s]={F:0,M:0};
      if(r.sexo==='F') m[s].F++; else if(r.sexo==='M') m[s].M++;
    });
    return Object.entries(m).map(([s,d])=>({sustancia:s,F:d.F,M:d.M,total:d.F+d.M})).sort((a,b)=>b.total-a.total);
  }, [filteredBase]);

  const sexoTotales = useMemo(() => [
    { name:'Femenino',  key:'F', numero_registros: filteredBase.filter(r=>r.sexo==='F').length },
    { name:'Masculino', key:'M', numero_registros: filteredBase.filter(r=>r.sexo==='M').length },
  ], [filteredBase]);

  const intencData = useMemo(() => {
    const m = {};
    filteredBase.forEach(r => {
      const s=r.grupos_sustancia_final; if(!s||s==='nan') return;
      if(!m[s]) m[s]={intencional:0,no_intencional:0};
      if(r.intencionalidad==='intencional') m[s].intencional++;
      else if(r.intencionalidad==='no_intencional') m[s].no_intencional++;
    });
    return Object.entries(m).map(([s,d])=>({
      sustancia:s, intencional:d.intencional, no_intencional:d.no_intencional,
      total:d.intencional+d.no_intencional,
      porcentaje_intencional:    (d.intencional+d.no_intencional)?((d.intencional/(d.intencional+d.no_intencional))*100).toFixed(1):0,
      porcentaje_no_intencional: (d.intencional+d.no_intencional)?((d.no_intencional/(d.intencional+d.no_intencional))*100).toFixed(1):0,
    })).sort((a,b)=>b.total-a.total);
  }, [filteredBase]);

  const intencTotales = useMemo(() => [
    { name:'Intencional',    key:'intencional',    numero_registros: filteredBase.filter(r=>r.intencionalidad==='intencional').length    },
    { name:'No Intencional', key:'no_intencional', numero_registros: filteredBase.filter(r=>r.intencionalidad==='no_intencional').length  },
  ], [filteredBase]);

  const filtSustancias = useMemo(() => {
    let d=[...sustancias];
    if(filtros.topN==='top5')  d=d.slice(0,5);
    if(filtros.topN==='top10') d=d.slice(0,10);
    return d;
  }, [sustancias, filtros.topN]);

  const [prodSearch,    setProdSearch]    = useState('');
  const [prodCat,       setProdCat]       = useState('__all__');
  const [prodMetodo,    setProdMetodo]    = useState('__all__');

  const prodFilt = useMemo(() => {
    let d=[...productosTodos];
    if(filtros.sustancia)    d=d.filter(x=>x.categoria===filtros.sustancia);
    if(prodSearch.trim())    d=d.filter(x=>String(x.producto).toLowerCase().includes(prodSearch.toLowerCase()));
    if(prodCat!=='__all__')  d=d.filter(x=>x.categoria===prodCat);
    if(prodMetodo!=='__all__') d=d.filter(x=>x.metodo_clasificacion===prodMetodo);
    return d;
  }, [filtros.sustancia, prodSearch, prodCat, prodMetodo]);

  const llmFilt = useMemo(() => {
    let d=[...resultadosLlm];
    if(filtros.sexo)      d=d.filter(r=>r.sexo===filtros.sexo);
    if(filtros.sustancia) d=d.filter(r=>String(r.grupos_sustancia_final)===filtros.sustancia);
    return d;
  }, [filtros.sexo, filtros.sustancia]);

  const uniqueSust    = useMemo(()=>[...new Set(sustancias.map(s=>s.sustancia))], [sustancias]);
  const uniqueCats    = useMemo(()=>[...new Set(productosTodos.map(p=>p.categoria))].sort(), []);
  const uniqueMetodos = useMemo(()=>[...new Set(resultadosLlm.map(r=>r.metodo_clasificacion).filter(Boolean))].sort(), []);
  const uniqueOrig    = useMemo(()=>[...new Set(resultadosLlm.map(r=>r.origen_hoja).filter(Boolean))].sort(), []);

  const scrollTo = (id) => {
    setActiveSection(id);
    document.getElementById(id)?.scrollIntoView({ behavior:'smooth', block:'start' });
    setSidebarOpen(false);
  };

  const fechaGen = metadata?.fecha_generacion
    ? new Date(metadata.fecha_generacion).toLocaleString('es-CO',{dateStyle:'long',timeStyle:'short'})
    : new Date().toLocaleString('es-CO',{dateStyle:'long',timeStyle:'short'});

  const hasFilters  = filtros.sexo||filtros.sustancia||filtros.intencionalidad;
  const filterCount = [filtros.sexo,filtros.sustancia,filtros.intencionalidad].filter(Boolean).length;

  const originalImages = [
    { src:'/images/sustancias.png',                     title:'Sustancias',                desc:'Conteo general de sustancias identificadas.'      },
    { src:'/images/top10_sustancias.png',               title:'Top 10 Sustancias',         desc:'Las 10 sustancias mas frecuentes.'                 },
    { src:'/images/conteo_sustancias_tipo.png',         title:'Conteo por Tipo',           desc:'Distribucion por tipo de sustancia.'               },
    { src:'/images/sexo.png',                           title:'Sexo',                      desc:'Distribucion total por sexo.'                     },
    { src:'/images/sustancias_por_sexo.png',            title:'Sustancias x Sexo',         desc:'Comparacion de sustancias entre sexos.'            },
    { src:'/images/heatmap_sustancia_sexo.png',         title:'Heatmap Sustancia x Sexo',  desc:'Mapa de calor por sexo.'                          },
    { src:'/images/intencionalidad.png',                title:'Intencionalidad',           desc:'Distribucion general de intencionalidad.'          },
    { src:'/images/sustancias_por_intencionalidad.png', title:'Sustancias x Intencionalidad',desc:'Comparacion intencional vs no intencional.'     },
  ];

  /* ── bar cell color ── */
  const barCell = (i, sustName) => {
    if (filtros.sustancia && filtros.sustancia === sustName) return '#22d3ee';
    if (filtros.sustancia && filtros.sustancia !== sustName) return 'rgba(129,140,248,0.35)';
    return 'url(#gPrimary)';
  };

  return (
    <div className="dashboard-container" data-theme={theme}>
      <GradDefs />
      <ThemeToggle theme={theme} onToggle={toggleTheme} />

      {/* Mobile toggle */}
      <button className="mobile-menu-btn" onClick={()=>setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen?'✕':'☰'}
      </button>

      {/* ══ SIDEBAR ══════════════════════════════════════════════════ */}
      <aside className={`sidebar ${sidebarOpen?'open':''}`}>
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">DS</div>
          <div>
            <div className="sidebar-logo-text">Dashboard</div>
            <div className="sidebar-logo-sub">Sustancias · SIVIGILA</div>
          </div>
        </div>
        <div className="sidebar-section">Navegacion</div>
        <ul className="sidebar-nav">
          {sections.map(s=>(
            <li key={s.id}>
              <a href={`#${s.id}`} className={activeSection===s.id?'active':''}
                onClick={e=>{e.preventDefault();scrollTo(s.id);}}>
                <span className="sidebar-nav-icon">{s.icon}</span>{s.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="sidebar-footer">
          {kpis.total_registros.toLocaleString('es-CO')} registros &middot; {kpis.categorias_detectadas} categorias
        </div>
      </aside>

      {/* ══ MAIN ═════════════════════════════════════════════════════ */}
      <main className="main-content">

        {/* HEADER */}
        <motion.div className="header-section"
          initial={{opacity:0,y:-24}} animate={{opacity:1,y:0}}
          transition={{duration:0.65,ease:[0.22,1,0.36,1]}}>
          <div className="header-grid"/>
          <div className="header-content">
            <div className="header-eyebrow">
              <span className="header-eyebrow-dot"/>
              Epidemiologia · Analisis de Clasificacion
            </div>
            <h1>Dashboard de Sustancias Psicoactivas</h1>
            <p>
              Tablero interactivo con filtros cruzados tipo Power BI. Haz clic en cualquier
              KPI, barra o grafico para filtrar todo el dashboard en cadena.
            </p>
            <div className="header-stats">
              <div className="header-stat">
                <span className="header-stat-dot"/>
                <span className="header-stat-value">{kpis.total_registros.toLocaleString('es-CO')}</span>
                <span>registros</span>
              </div>
              <div className="header-stat">
                <span className="header-stat-dot" style={{background:'#22d3ee',boxShadow:'0 0 6px #22d3ee'}}/>
                <span className="header-stat-value">{kpis.categorias_detectadas}</span>
                <span>categorias</span>
              </div>
              <div className="header-stat">
                <span className="header-stat-dot" style={{background:'#f472b6',boxShadow:'0 0 6px #f472b6'}}/>
                <span className="header-stat-value">{kpis.sexo_f?.toLocaleString('es-CO')}</span>
                <span>Femenino</span>
              </div>
              <div className="header-stat">
                <span className="header-stat-dot" style={{background:'#818cf8',boxShadow:'0 0 6px #818cf8'}}/>
                <span className="header-stat-value">{kpis.sexo_m?.toLocaleString('es-CO')}</span>
                <span>Masculino</span>
              </div>
              <div className="header-stat">
                <span className="header-stat-dot" style={{background:'#f87171',boxShadow:'0 0 6px #f87171'}}/>
                <span className="header-stat-value">{kpis.pct_intencional}%</span>
                <span>intencional</span>
              </div>
            </div>
            <div className="header-date">Generado: {fechaGen}</div>
          </div>
        </motion.div>

        {/* ACTIVE FILTERS PILL BAR */}
        <AnimatePresence>
          {hasFilters && (
            <motion.div className="active-filters-bar"
              initial={{opacity:0,height:0,marginBottom:0}}
              animate={{opacity:1,height:'auto',marginBottom:'1.5rem'}}
              exit={{opacity:0,height:0,marginBottom:0}}
              transition={{duration:0.28}}>
              <span className="filter-bar-label">{filterCount} filtro{filterCount>1?'s':''} activo{filterCount>1?'s':''}</span>
              {filtros.sustancia      && <span className="filter-chip" onClick={()=>clearOne('sustancia')}>Sustancia: {filtros.sustancia} x</span>}
              {filtros.sexo           && <span className="filter-chip" onClick={()=>clearOne('sexo')}>Sexo: {filtros.sexo==='F'?'Femenino':'Masculino'} x</span>}
              {filtros.intencionalidad && <span className="filter-chip" onClick={()=>clearOne('intencionalidad')}>Intent.: {filtros.intencionalidad} x</span>}
              <span className="filter-chip filter-chip-clear" onClick={clearAll}>Limpiar todo</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* FILTER PANEL */}
        <div className="filter-panel">
          <div className="filter-panel-title">Controles Globales (filtros cruzados)</div>
          <div className="filters-row">
            <div className="filter-group">
              <span className="filter-label">Sustancia</span>
              <select className="filter-select" value={filtros.sustancia||''} onChange={e=>setFilter('sustancia',e.target.value||null)}>
                <option value="">Todas</option>
                {uniqueSust.map(s=><option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="filter-group">
              <span className="filter-label">Sexo</span>
              <select className="filter-select" value={filtros.sexo||''} onChange={e=>setFilter('sexo',e.target.value||null)}>
                <option value="">Todos</option>
                <option value="F">Femenino</option>
                <option value="M">Masculino</option>
              </select>
            </div>
            <div className="filter-group">
              <span className="filter-label">Intencionalidad</span>
              <select className="filter-select" value={filtros.intencionalidad||''} onChange={e=>setFilter('intencionalidad',e.target.value||null)}>
                <option value="">Todas</option>
                <option value="intencional">Intencional</option>
                <option value="no_intencional">No intencional</option>
              </select>
            </div>
            <div className="filter-group">
              <span className="filter-label">Top N</span>
              <select className="filter-select" value={filtros.topN} onChange={e=>setFiltros(p=>({...p,topN:e.target.value}))}>
                <option value="todas">Todas</option>
                <option value="top5">Top 5</option>
                <option value="top10">Top 10</option>
              </select>
            </div>
            {hasFilters && (
              <div className="filter-group" style={{justifyContent:'flex-end'}}>
                <span className="filter-label" style={{visibility:'hidden'}}>x</span>
                <button className="btn btn-secondary" onClick={clearAll}>Limpiar</button>
              </div>
            )}
          </div>
        </div>

        {/* ══ KPIs ══════════════════════════════════════════════════ */}
        <motion.section id="kpis" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F4CA}'} title="KPIs Principales" badge={hasFilters?'filtrados':null}/>
          <motion.div className="kpi-grid" variants={gridVar} initial="hidden" animate="visible">
            {[
              {icon:'\u{1F4CB}', label:'Total Registros',    value:kpis.total_registros,          color:'primary'},
              {icon:'\u26A0',    label:'Intencionales',      value:kpis.intencional,               color:'danger',   sub:`${kpis.pct_intencional}%`,    fn:()=>setFilter('intencionalidad','intencional'),    active:filtros.intencionalidad==='intencional'},
              {icon:'\u2705',    label:'No Intencionales',   value:kpis.no_intencional,            color:'success',  sub:`${kpis.pct_no_intencional}%`, fn:()=>setFilter('intencionalidad','no_intencional'), active:filtros.intencionalidad==='no_intencional'},
              {icon:'\u{1F947}', label:'Sustancia Principal',value:kpis.sustancia_mas_frecuente,  color:'warning',  fn:()=>setFilter('sustancia',kpis.sustancia_mas_frecuente), active:filtros.sustancia===kpis.sustancia_mas_frecuente},
              {icon:'\u{1F948}', label:'2a Sustancia',       value:kpis.segunda_sustancia,        color:'violet',   fn:()=>setFilter('sustancia',kpis.segunda_sustancia),       active:filtros.sustancia===kpis.segunda_sustancia},
              {icon:'\u{1F949}', label:'3a Sustancia',       value:kpis.tercera_sustancia,        color:'cyan',     fn:()=>setFilter('sustancia',kpis.tercera_sustancia),       active:filtros.sustancia===kpis.tercera_sustancia},
              {icon:'\u{1F3AF}', label:'Mas Intencional',    value:sustanciaMasIntencional,       color:'danger',   fn:()=>setFilter('sustancia',sustanciaMasIntencional),      active:filtros.sustancia===sustanciaMasIntencional},
              {icon:'\u2640',    label:'Sexo Femenino',      value:kpis.sexo_f,                   color:'pink',     fn:()=>setFilter('sexo','F'), active:filtros.sexo==='F'},
              {icon:'\u2642',    label:'Sexo Masculino',     value:kpis.sexo_m,                   color:'primary',  fn:()=>setFilter('sexo','M'), active:filtros.sexo==='M'},
              {icon:'\u{1F3F7}', label:'Categorias',         value:kpis.categorias_detectadas,    color:'cyan'},
            ].map((k,i)=>(
              <KpiCard key={i} icon={k.icon} label={k.label} value={k.value}
                sub={k.sub} color={k.color} onClick={k.fn} active={k.active}/>
            ))}
          </motion.div>
        </motion.section>

        {/* ══ SUSTANCIAS ═══════════════════════════════════════════ */}
        <motion.section id="sustancias" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F9EA}'} title="Analisis por Tipo de Sustancia"/>
          <div className="card">
            <div className="card-header">
              <div className="card-title">Conteo por Sustancia <span className="card-badge">clic en barra = filtrar</span></div>
              <div className="card-hint">{filtSustancias.length} categorias</div>
            </div>
            <ResponsiveContainer width="100%" height={Math.max(320, filtSustancias.length*30)}>
              <BarChart data={filtSustancias} layout="vertical" margin={{left:8,right:24,top:4,bottom:4}}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false}/>
                <XAxis type="number" tick={{fontSize:11,fill:'#475569'}} axisLine={{stroke:'rgba(255,255,255,0.06)'}} tickLine={false}/>
                <YAxis dataKey="sustancia" type="category" width={195} tick={{fontSize:11,fontWeight:500,fill:'#64748b'}} axisLine={false} tickLine={false}/>
                <Tooltip content={<DarkTooltip/>}/>
                <Bar dataKey="numero_registros" name="Registros" radius={[0,6,6,0]} barSize={18}
                  onClick={d=>setFilter('sustancia',d?.sustancia||d?.payload?.sustancia)}
                  style={{cursor:'pointer'}}>
                  {filtSustancias.map((item,i)=>(
                    <Cell key={i} fill={barCell(i,item.sustancia)}/>
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.section>

        {/* ══ SEXO ══════════════════════════════════════════════════ */}
        <motion.section id="sexo" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u26A5'} title="Analisis por Sexo"/>
          <div className="kpi-grid" style={{gridTemplateColumns:'1fr 1fr',maxWidth:480,marginBottom:'1.25rem'}}>
            <KpiCard icon="\u2640" label="Total Femenino"  value={sexoTotales[0]?.numero_registros}
              sub={`${kpis.total_registros?((sexoTotales[0]?.numero_registros/kpis.total_registros)*100).toFixed(1):0}%`}
              color="pink" onClick={()=>setFilter('sexo','F')} active={filtros.sexo==='F'}/>
            <KpiCard icon="\u2642" label="Total Masculino" value={sexoTotales[1]?.numero_registros}
              sub={`${kpis.total_registros?((sexoTotales[1]?.numero_registros/kpis.total_registros)*100).toFixed(1):0}%`}
              color="primary" onClick={()=>setFilter('sexo','M')} active={filtros.sexo==='M'}/>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'1.25rem'}}>
            <div className="card">
              <div className="card-header">
                <div className="card-title">Distribucion por Sexo</div>
                <div className="card-hint">clic = filtrar</div>
              </div>
              <ResponsiveContainer width="100%" height={270}>
                <PieChart>
                  <Pie data={sexoTotales} dataKey="numero_registros" nameKey="name"
                    cx="50%" cy="50%" innerRadius={62} outerRadius={100}
                    activeIndex={pieSexoIdx} activeShape={ActiveDonutShape}
                    onMouseEnter={(_,i)=>setPieSexoIdx(i)}
                    onClick={d=>setFilter('sexo',d?.key||(d?.name==='Femenino'?'F':'M'))}
                    style={{cursor:'pointer'}}>
                    <Cell fill="#f472b6"/>
                    <Cell fill="#818cf8"/>
                  </Pie>
                  <Tooltip content={<DarkTooltip/>}/>
                  <Legend iconType="circle" iconSize={8}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-header">
                <div className="card-title">Sustancias x Sexo (Top 10)</div>
              </div>
              <ResponsiveContainer width="100%" height={270}>
                <BarChart data={sexoData.slice(0,10)} layout="vertical" margin={{left:8,right:12}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false}/>
                  <XAxis type="number" tick={{fontSize:10,fill:'#475569'}} axisLine={{stroke:'rgba(255,255,255,0.06)'}} tickLine={false}/>
                  <YAxis dataKey="sustancia" type="category" width={160} tick={{fontSize:10,fill:'#64748b'}} axisLine={false} tickLine={false}/>
                  <Tooltip content={<DarkTooltip/>}/>
                  <Legend iconType="circle" iconSize={7}/>
                  <Bar dataKey="F" name="Femenino"  fill="url(#gPink)"    radius={[0,3,3,0]} barSize={10}/>
                  <Bar dataKey="M" name="Masculino" fill="url(#gPrimary)" radius={[0,3,3,0]} barSize={10}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {sexoData.length>10&&(
            <div className="card">
              <div className="card-header"><div className="card-title">Todas las sustancias x Sexo</div></div>
              <ResponsiveContainer width="100%" height={Math.max(340,sexoData.length*26)}>
                <BarChart data={sexoData} layout="vertical" margin={{left:8,right:16}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false}/>
                  <XAxis type="number" tick={{fontSize:11,fill:'#475569'}} axisLine={{stroke:'rgba(255,255,255,0.06)'}} tickLine={false}/>
                  <YAxis dataKey="sustancia" type="category" width={185} tick={{fontSize:11,fill:'#64748b'}} axisLine={false} tickLine={false}/>
                  <Tooltip content={<DarkTooltip/>}/>
                  <Legend iconType="circle" iconSize={8}/>
                  <Bar dataKey="F" name="Femenino"  fill="url(#gPink)"    radius={[0,4,4,0]} barSize={14}/>
                  <Bar dataKey="M" name="Masculino" fill="url(#gPrimary)" radius={[0,4,4,0]} barSize={14}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </motion.section>

        {/* ══ INTENCIONALIDAD ══════════════════════════════════════ */}
        <motion.section id="intencionalidad" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F3AF}'} title="Analisis por Intencionalidad"/>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'1.25rem'}}>
            <div className="card">
              <div className="card-header">
                <div className="card-title">Distribucion de Intencionalidad</div>
                <div className="card-hint">clic = filtrar</div>
              </div>
              <ResponsiveContainer width="100%" height={270}>
                <PieChart>
                  <Pie data={intencTotales} dataKey="numero_registros" nameKey="name"
                    cx="50%" cy="50%" innerRadius={62} outerRadius={100}
                    activeIndex={pieIntencIdx} activeShape={ActiveDonutShape}
                    onMouseEnter={(_,i)=>setPieIntencIdx(i)}
                    onClick={d=>setFilter('intencionalidad',d?.key||(d?.name?.toLowerCase().startsWith('no')?'no_intencional':'intencional'))}
                    style={{cursor:'pointer'}}>
                    <Cell fill="#f87171"/>
                    <Cell fill="#34d399"/>
                  </Pie>
                  <Tooltip content={<DarkTooltip/>}/>
                  <Legend iconType="circle" iconSize={8}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-header"><div className="card-title">Top Sustancias x Intencionalidad</div></div>
              <ResponsiveContainer width="100%" height={270}>
                <BarChart data={intencData.slice(0,8)} layout="vertical" margin={{left:8,right:12}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false}/>
                  <XAxis type="number" tick={{fontSize:10,fill:'#475569'}} axisLine={{stroke:'rgba(255,255,255,0.06)'}} tickLine={false}/>
                  <YAxis dataKey="sustancia" type="category" width={162} tick={{fontSize:10,fill:'#64748b'}} axisLine={false} tickLine={false}/>
                  <Tooltip content={<DarkTooltip/>}/>
                  <Legend iconType="circle" iconSize={7}/>
                  <Bar dataKey="intencional"    name="Intencional"    stackId="a" fill="url(#gDanger)"  barSize={16}/>
                  <Bar dataKey="no_intencional" name="No Intencional" stackId="a" fill="url(#gSuccess)" radius={[4,4,0,0]} barSize={16}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {intencData.length>8&&(
            <div className="card">
              <div className="card-header"><div className="card-title">Todas las sustancias x Intencionalidad</div></div>
              <ResponsiveContainer width="100%" height={Math.max(340,intencData.length*26)}>
                <BarChart data={intencData} layout="vertical" margin={{left:8,right:16}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false}/>
                  <XAxis type="number" tick={{fontSize:11,fill:'#475569'}} axisLine={{stroke:'rgba(255,255,255,0.06)'}} tickLine={false}/>
                  <YAxis dataKey="sustancia" type="category" width={185} tick={{fontSize:11,fill:'#64748b'}} axisLine={false} tickLine={false}/>
                  <Tooltip content={<DarkTooltip/>}/>
                  <Legend iconType="circle" iconSize={8}/>
                  <Bar dataKey="intencional"    name="Intencional"    stackId="a" fill="url(#gDanger)"  barSize={18}/>
                  <Bar dataKey="no_intencional" name="No Intencional" stackId="a" fill="url(#gSuccess)" radius={[4,4,0,0]} barSize={18}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="card">
            <div className="card-header"><div className="card-title">Tabla de Intencionalidad por Sustancia</div></div>
            <DataTable data={intencData} columns={[
              {key:'sustancia',label:'Sustancia'},{key:'total',label:'Total'},
              {key:'intencional',label:'Intencional'},{key:'no_intencional',label:'No Intencional'},
              {key:'porcentaje_intencional',label:'% Intencional'},{key:'porcentaje_no_intencional',label:'% No Intencional'},
            ]} exportFilename="intencionalidad_por_sustancia.csv" showFilters={false}/>
          </div>
        </motion.section>

        {/* ══ PRODUCTOS ════════════════════════════════════════════ */}
        <motion.section id="productos" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F4E6}'} title="Analisis de Productos"/>
          <div className="card">
            <div className="card-header">
              <div className="card-title">Buscar Productos</div>
              <div className="card-hint">{prodFilt.length} resultados</div>
            </div>
            <div className="filters-row" style={{marginBottom:'1.25rem'}}>
              <div className="filter-group">
                <span className="filter-label">Buscar</span>
                <input type="text" className="filter-input" placeholder="Nombre del producto..."
                  value={prodSearch} onChange={e=>setProdSearch(e.target.value)}
                  style={{minWidth:200,backgroundImage:'none',paddingRight:'0.875rem'}}/>
              </div>
              <div className="filter-group">
                <span className="filter-label">Categoria</span>
                <select className="filter-select" value={prodCat} onChange={e=>setProdCat(e.target.value)}>
                  <option value="__all__">Todas</option>
                  {uniqueCats.map(c=><option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="filter-group">
                <span className="filter-label">Metodo</span>
                <select className="filter-select" value={prodMetodo} onChange={e=>setProdMetodo(e.target.value)}>
                  <option value="__all__">Todos</option>
                  <option value="deterministic">Deterministic</option>
                  <option value="llm">LLM</option>
                  <option value="cache">Cache</option>
                  <option value="blacklist">Blacklist</option>
                  <option value="default">Default</option>
                </select>
              </div>
              <div className="filter-group" style={{justifyContent:'flex-end'}}>
                <span className="filter-label" style={{visibility:'hidden'}}>x</span>
                <div style={{display:'flex',gap:'0.5rem'}}>
                  <button className="btn btn-secondary" onClick={()=>{setProdSearch('');setProdCat('__all__');setProdMetodo('__all__');}}>Limpiar</button>
                  <button className="btn btn-primary" onClick={()=>{
                    const h=['categoria','producto','conteo','metodo_clasificacion'].join(',');
                    const r=prodFilt.map(x=>`"${x.categoria}","${x.producto}","${x.conteo}","${x.metodo_clasificacion}"`);
                    const csv=[h,...r].join('\n');
                    const b=new Blob([csv],{type:'text/csv;charset=utf-8;'});
                    const l=document.createElement('a');l.href=URL.createObjectURL(b);l.download='productos.csv';l.click();
                  }}>Exportar CSV</button>
                </div>
              </div>
            </div>
            <DataTable data={prodFilt}
              columns={[{key:'categoria',label:'Categoria'},{key:'producto',label:'Producto'},{key:'conteo',label:'Conteo'},{key:'metodo_clasificacion',label:'Metodo'}]}
              exportFilename="productos.csv" showFilters={false} showSearch={false} showExport={false}/>
          </div>
        </motion.section>

        {/* ══ TABLA ════════════════════════════════════════════════ */}
        <motion.section id="tabla" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F50D}'} title="Tabla Exploratoria" badge={hasFilters?'filtrada':null}/>
          <div className="card">
            <div className="card-header">
              <div className="card-title">Resultados de Clasificacion Avanzada</div>
              <div className="card-hint">{llmFilt.length.toLocaleString('es-CO')} registros</div>
            </div>
            <DataTable data={llmFilt} columns={[
              {key:'origen_hoja',label:'Origen'},{key:'fec_not',label:'Fecha'},{key:'sexo',label:'Sexo'},{key:'edad',label:'Edad'},
              {key:'nom_pro',label:'Producto'},{key:'grupos_sustancia_final',label:'Sustancia Final'},{key:'metodo_clasificacion',label:'Metodo'},
            ]} filterOptions={{sexo:['F','M'],metodo_clasificacion:uniqueMetodos,origen_hoja:uniqueOrig.slice(0,20)}}
            exportFilename="resultados_clasificacion.csv"/>
          </div>
          <div className="card">
            <div className="card-header">
              <div className="card-title">Base Completa con Intencionalidad</div>
              <div className="card-hint">{filteredBase.length.toLocaleString('es-CO')} registros</div>
            </div>
            <DataTable data={filteredBase} columns={[
              {key:'origen_hoja',label:'Origen'},{key:'fec_not',label:'Fecha'},{key:'sexo',label:'Sexo'},{key:'edad',label:'Edad'},
              {key:'nom_pro',label:'Producto'},{key:'grupos_sustancia_final',label:'Sustancia'},{key:'intencionalidad',label:'Intencionalidad'},{key:'metodo_clasificacion',label:'Metodo'},
            ]} filterOptions={{sexo:['F','M'],intencionalidad:['intencional','no_intencional']}}
            exportFilename="base_completa.csv"/>
          </div>
        </motion.section>

        {/* ══ HALLAZGOS ════════════════════════════════════════════ */}
        <motion.section id="hallazgos" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F4A1}'} title="Hallazgos Principales"/>
          <div className="findings-grid">
            <div className="findings-box" style={{'--findings-color':'var(--primary)'}}>
              <h4>Resumen del Analisis</h4>
              <p>El analisis abarca <strong>{kpis.total_registros.toLocaleString('es-CO')} registros</strong> en <strong>{kpis.categorias_detectadas} categorias</strong>. La sustancia mas frecuente es <strong>{kpis.sustancia_mas_frecuente}</strong>, seguida de <strong>{kpis.segunda_sustancia}</strong> y <strong>{kpis.tercera_sustancia}</strong>.</p>
            </div>
            <div className="findings-box" style={{'--findings-color':'var(--pink)'}}>
              <h4>Distribucion por Sexo</h4>
              <ul>
                <li>Femenino: <strong>{kpis.sexo_f?.toLocaleString('es-CO')}</strong> registros ({kpis.total_registros?((kpis.sexo_f/kpis.total_registros)*100).toFixed(1):0}%)</li>
                <li>Masculino: <strong>{kpis.sexo_m?.toLocaleString('es-CO')}</strong> registros ({kpis.total_registros?((kpis.sexo_m/kpis.total_registros)*100).toFixed(1):0}%)</li>
                <li>Mujeres predominan en medicamentos_no_SPA y tranquilizantes; hombres en alcohol, cocaina y cannabinoides.</li>
              </ul>
            </div>
            <div className="findings-box" style={{'--findings-color':'var(--danger)'}}>
              <h4>Intencionalidad</h4>
              <ul>
                <li><strong>{kpis.intencional?.toLocaleString('es-CO')}</strong> casos intencionales ({kpis.pct_intencional}%)</li>
                <li><strong>{kpis.no_intencional?.toLocaleString('es-CO')}</strong> casos no intencionales ({kpis.pct_no_intencional}%)</li>
                <li>Sustancia con mayor proporcion intencional: <strong>{sustanciaMasIntencional}</strong></li>
              </ul>
            </div>
            <div className="findings-box" style={{'--findings-color':'var(--warning)'}}>
              <h4>Limitaciones</h4>
              <ul>
                <li>La categoria "otros" puede enmascarar patrones especificos.</li>
                <li>Datos de notificacion epidemiologica, sujetos a sesgos de subregistro.</li>
                <li>La clasificacion LLM puede variar en categorias ambiguas.</li>
              </ul>
            </div>
          </div>
        </motion.section>

        {/* ══ GRAFICAS ORIGINALES ══════════════════════════════════ */}
        <motion.section id="originales" variants={secVar} initial="hidden" whileInView="visible" viewport={{once:true,margin:'-60px'}}>
          <SH icon={'\u{1F5BC}'} title="Graficas Originales de la Corrida"/>
          <div className="gallery-grid">
            {originalImages.map((img,idx)=>(
              <motion.div className="gallery-card" key={idx}
                initial={{opacity:0,y:22}} whileInView={{opacity:1,y:0}}
                transition={{delay:idx*0.06,duration:0.42,ease:[0.22,1,0.36,1]}}
                viewport={{once:true}}>
                <img src={img.src} alt={img.title} loading="lazy"/>
                <div className="caption">
                  <h4>{img.title}</h4>
                  <p>{img.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <footer className="dashboard-footer">
          Dashboard generado automaticamente desde outputs/clasificaciones_conteo &middot; {fechaGen}
        </footer>
      </main>

      <ChatBot/>
    </div>
  );
};

export default App;
