import React, { useState, useMemo, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import KpiCard from './components/KpiCard';
import DataTable from './components/DataTable';
import ChatBot from './components/ChatBot';
import {
  kpis as baseKpis, sustancias as baseSustancias, intencionalidad as baseIntenc,
  sexo as baseSexo, sustanciasPorIntencionalidad as baseSustInt,
  sustanciaSexo as baseSustSexo, productosTodos, conteoCategorias as baseConteoCat,
  resultadosLlm, resumenCategorias, baseCompleta, metadata
} from './data/data';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#3b82f6', '#14b8a6', '#d946ef'];

const sections = [
  { id: 'kpis', label: 'KPIs', icon: '📊' },
  { id: 'sustancias', label: 'Por Sustancia', icon: '🧪' },
  { id: 'sexo', label: 'Por Sexo', icon: '⚥' },
  { id: 'intencionalidad', label: 'Por Intencionalidad', icon: '🎯' },
  { id: 'productos', label: 'Productos', icon: '📦' },
  { id: 'tabla', label: 'Tabla Exploratoria', icon: '🔍' },
  { id: 'hallazgos', label: 'Hallazgos', icon: '💡' },
  { id: 'originales', label: 'Gráficas Originales', icon: '🖼' },
];

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('kpis');

  // ─── FILTROS GLOBALES CRUZADOS ────────────────────────────────────
  const [filtros, setFiltros] = useState({ sexo: null, sustancia: null, intencionalidad: null, topN: 'todas' });

  const setFilter = useCallback((key, value) => {
    setFiltros(prev => {
      if (prev[key] === value) return { ...prev, [key]: null };
      return { ...prev, [key]: value };
    });
  }, []);

  const clearAllFilters = useCallback(() => {
    setFiltros({ sexo: null, sustancia: null, intencionalidad: null, topN: 'todas' });
  }, []);

  const clearFilter = useCallback((key) => {
    setFiltros(prev => ({ ...prev, [key]: null }));
  }, []);

  // ─── DATOS FILTRADOS DESDE BASE COMPLETA ──────────────────────────
  const filteredBase = useMemo(() => {
    let data = baseCompleta;
    if (filtros.sexo) data = data.filter(r => r.sexo === filtros.sexo);
    if (filtros.sustancia) data = data.filter(r => String(r.grupos_sustancia_final) === filtros.sustancia);
    if (filtros.intencionalidad) data = data.filter(r => r.intencionalidad === filtros.intencionalidad);
    return data;
  }, [filtros.sexo, filtros.sustancia, filtros.intencionalidad]);

  // ─── KPIs RECALCULADOS ───────────────────────────────────────────
  const kpis = useMemo(() => {
    const total = filteredBase.length;
    const int = filteredBase.filter(r => r.intencionalidad === 'intencional').length;
    const noint = filteredBase.filter(r => r.intencionalidad === 'no_intencional').length;
    const sexoF = filteredBase.filter(r => r.sexo === 'F').length;
    const sexoM = filteredBase.filter(r => r.sexo === 'M').length;
    const sustMap = {};
    filteredBase.forEach(r => {
      const s = r.grupos_sustancia_final;
      if (!s || s === 'nan') return;
      sustMap[s] = (sustMap[s] || 0) + 1;
    });
    const sustArr = Object.entries(sustMap).map(([s, n]) => ({ sustancia: s, numero_registros: n })).sort((a, b) => b.numero_registros - a.numero_registros);
    return {
      total_registros: total, intencional: int, no_intencional: noint,
      pct_intencional: total ? ((int / total) * 100).toFixed(1) : 0,
      pct_no_intencional: total ? ((noint / total) * 100).toFixed(1) : 0,
      sexo_f: sexoF, sexo_m: sexoM,
      sustancia_mas_frecuente: sustArr[0]?.sustancia || '-',
      segunda_sustancia: sustArr[1]?.sustancia || '-',
      tercera_sustancia: sustArr[2]?.sustancia || '-',
      categorias_detectadas: sustArr.length,
    };
  }, [filteredBase]);

  const sustancias = useMemo(() => {
    const map = {};
    filteredBase.forEach(r => {
      const s = r.grupos_sustancia_final;
      if (!s || s === 'nan') return;
      map[s] = (map[s] || 0) + 1;
    });
    return Object.entries(map).map(([k, v]) => ({ sustancia: k, numero_registros: v })).sort((a, b) => b.numero_registros - a.numero_registros);
  }, [filteredBase]);

  const sustanciaMasIntencional = useMemo(() => {
    const map = {};
    filteredBase.forEach(r => {
      const s = r.grupos_sustancia_final;
      if (!s || s === 'nan') return;
      if (!map[s]) map[s] = { total: 0, intencional: 0 };
      map[s].total++;
      if (r.intencionalidad === 'intencional') map[s].intencional++;
    });
    let best = null;
    Object.entries(map).forEach(([s, d]) => {
      if (d.total < 10) return;
      const pct = d.intencional / d.total;
      if (!best || pct > best.pct) best = { sustancia: s, pct };
    });
    return best?.sustancia || '-';
  }, [filteredBase]);

  const sexoData = useMemo(() => {
    const map = {};
    filteredBase.forEach(r => {
      const s = r.grupos_sustancia_final;
      if (!s || s === 'nan') return;
      if (!map[s]) map[s] = { F: 0, M: 0 };
      if (r.sexo === 'F') map[s].F++;
      else if (r.sexo === 'M') map[s].M++;
    });
    return Object.entries(map).map(([s, d]) => ({ sustancia: s, F: d.F, M: d.M, total: d.F + d.M })).sort((a, b) => b.total - a.total);
  }, [filteredBase]);

  const sexoTotales = useMemo(() => [
    { sexo: 'F', numero_registros: filteredBase.filter(r => r.sexo === 'F').length },
    { sexo: 'M', numero_registros: filteredBase.filter(r => r.sexo === 'M').length },
  ], [filteredBase]);

  const intencionalidadData = useMemo(() => {
    const map = {};
    filteredBase.forEach(r => {
      const s = r.grupos_sustancia_final;
      if (!s || s === 'nan') return;
      if (!map[s]) map[s] = { intencional: 0, no_intencional: 0 };
      if (r.intencionalidad === 'intencional') map[s].intencional++;
      else if (r.intencionalidad === 'no_intencional') map[s].no_intencional++;
    });
    return Object.entries(map).map(([s, d]) => ({
      sustancia: s, intencional: d.intencional, no_intencional: d.no_intencional, total: d.intencional + d.no_intencional,
      porcentaje_intencional: (d.intencional + d.no_intencional) ? ((d.intencional / (d.intencional + d.no_intencional)) * 100).toFixed(1) : 0,
      porcentaje_no_intencional: (d.intencional + d.no_intencional) ? ((d.no_intencional / (d.intencional + d.no_intencional)) * 100).toFixed(1) : 0,
    })).sort((a, b) => b.total - a.total);
  }, [filteredBase]);

  const intencionalidadTotales = useMemo(() => [
    { intencionalidad: 'intencional', numero_registros: filteredBase.filter(r => r.intencionalidad === 'intencional').length },
    { intencionalidad: 'no_intencional', numero_registros: filteredBase.filter(r => r.intencionalidad === 'no_intencional').length },
  ], [filteredBase]);

  const filteredSustancias = useMemo(() => {
    let data = [...sustancias];
    if (filtros.topN === 'top5') data = data.slice(0, 5);
    else if (filtros.topN === 'top10') data = data.slice(0, 10);
    return data;
  }, [sustancias, filtros.topN]);

  const [prodSearch, setProdSearch] = useState('');
  const [prodCategoria, setProdCategoria] = useState('__all__');
  const [prodMetodo, setProdMetodo] = useState('__all__');

  const productosFiltrados = useMemo(() => {
    let data = [...productosTodos];
    if (filtros.sustancia) data = data.filter(d => d.categoria === filtros.sustancia);
    if (prodSearch.trim()) data = data.filter(d => String(d.producto).toLowerCase().includes(prodSearch.toLowerCase()));
    if (prodCategoria !== '__all__') data = data.filter(d => d.categoria === prodCategoria);
    if (prodMetodo !== '__all__') data = data.filter(d => d.metodo_clasificacion === prodMetodo);
    return data;
  }, [filtros.sustancia, prodSearch, prodCategoria, prodMetodo]);

  const resultadosLlmFiltrados = useMemo(() => {
    let data = [...resultadosLlm];
    if (filtros.sexo) data = data.filter(r => r.sexo === filtros.sexo);
    if (filtros.sustancia) data = data.filter(r => String(r.grupos_sustancia_final) === filtros.sustancia);
    return data;
  }, [filtros.sexo, filtros.sustancia]);

  const uniqueSustancias = useMemo(() => [...new Set(sustancias.map(s => s.sustancia))], [sustancias]);
  const uniqueCategoriasProductos = useMemo(() => [...new Set(productosTodos.map(p => p.categoria))].sort(), []);
  const uniqueMetodos = useMemo(() => [...new Set(resultadosLlm.map(r => r.metodo_clasificacion).filter(Boolean))].sort(), []);
  const uniqueOrigenes = useMemo(() => [...new Set(resultadosLlm.map(r => r.origen_hoja).filter(Boolean))].sort(), []);

  const scrollTo = (id) => { setActiveSection(id); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); setSidebarOpen(false); };

  const fechaGeneracion = metadata?.fecha_generacion
    ? new Date(metadata.fecha_generacion).toLocaleString('es-CO', { dateStyle: 'long', timeStyle: 'short' })
    : new Date().toLocaleString('es-CO', { dateStyle: 'long', timeStyle: 'short' });

  const hasActiveFilters = filtros.sexo || filtros.sustancia || filtros.intencionalidad;
  const filterCount = [filtros.sexo, filtros.sustancia, filtros.intencionalidad].filter(Boolean).length;

  const originalImages = [
    { src: '/images/sustancias.png', title: 'Sustancias', desc: 'Conteo general de sustancias identificadas.' },
    { src: '/images/top10_sustancias.png', title: 'Top 10 Sustancias', desc: 'Las 10 sustancias más frecuentes.' },
    { src: '/images/conteo_sustancias_tipo.png', title: 'Conteo por Tipo', desc: 'Distribución por tipo de sustancia.' },
    { src: '/images/sexo.png', title: 'Sexo', desc: 'Distribución total por sexo.' },
    { src: '/images/sustancias_por_sexo.png', title: 'Sustancias × Sexo', desc: 'Comparación de sustancias entre sexos.' },
    { src: '/images/heatmap_sustancia_sexo.png', title: 'Heatmap Sustancia × Sexo', desc: 'Mapa de calor por sexo.' },
    { src: '/images/intencionalidad.png', title: 'Intencionalidad', desc: 'Distribución general de intencionalidad.' },
    { src: '/images/sustancias_por_intencionalidad.png', title: 'Sustancias × Intencionalidad', desc: 'Comparación intencional vs no intencional.' },
  ];

  return (
    <div className="dashboard-container">
      <button className="mobile-menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>{sidebarOpen ? '✕' : '☰'}</button>
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-logo"><div className="sidebar-logo-icon">DS</div><div><div className="sidebar-logo-text">Dashboard</div><div className="sidebar-logo-sub">Sustancias</div></div></div>
        <div className="sidebar-section">Navegación</div>
        <ul className="sidebar-nav">
          {sections.map(s => (<li key={s.id}><a href={`#${s.id}`} className={activeSection === s.id ? 'active' : ''} onClick={(e) => { e.preventDefault(); scrollTo(s.id); }}><span className="sidebar-nav-icon">{s.icon}</span>{s.label}</a></li>))}
        </ul>
      </aside>

      <main className="main-content">
        <div className="header-section">
          <div className="header-decoration" /><div className="header-decoration-inner" />
          <h1>Dashboard de Análisis de Clasificación de Sustancias</h1>
          <p>Tablero interactivo con filtros cruzados tipo Power BI. Haz clic en cualquier KPI, barra o gráfico para filtrar todo el dashboard en cadena.</p>
          <div className="header-badges">
            <div className="header-badge">📋 <span className="header-badge-value">{kpis.total_registros.toLocaleString('es-CO')}</span> registros</div>
            <div className="header-badge">🏷 <span className="header-badge-value">{kpis.categorias_detectadas}</span> categorías</div>
            <div className="header-badge">♀ <span className="header-badge-value">{kpis.sexo_f?.toLocaleString('es-CO')}</span> F</div>
            <div className="header-badge">♂ <span className="header-badge-value">{kpis.sexo_m?.toLocaleString('es-CO')}</span> M</div>
          </div>
          <div className="header-date">🕐 {fechaGeneracion}</div>
        </div>

        {hasActiveFilters && (
          <div className="active-filters-bar">
            <span className="filter-bar-label">{filterCount} filtro{filterCount > 1 ? 's' : ''} activo{filterCount > 1 ? 's' : ''}</span>
            {filtros.sustancia && (<span className="filter-chip" onClick={() => clearFilter('sustancia')}>🧪 {filtros.sustancia} ✕</span>)}
            {filtros.sexo && (<span className="filter-chip" onClick={() => clearFilter('sexo')}>⚥ Sexo: {filtros.sexo === 'F' ? 'Femenino' : 'Masculino'} ✕</span>)}
            {filtros.intencionalidad && (<span className="filter-chip" onClick={() => clearFilter('intencionalidad')}>🎯 Intencionalidad: {filtros.intencionalidad} ✕</span>)}
            <span className="filter-chip filter-chip-clear" onClick={clearAllFilters}>🗑 Limpiar todo</span>
          </div>
        )}

        <div className="card" style={{ animationDelay: '0.05s' }}>
          <div className="card-title">🎚 Filtros y Controles</div>
          <div className="filters-bar">
            <label>Sustancia:</label>
            <select value={filtros.sustancia || ''} onChange={(e) => setFilter('sustancia', e.target.value || null)}>
              <option value="">Todas</option>
              {uniqueSustancias.map(s => (<option key={s} value={s}>{s}</option>))}
            </select>
            <label>Sexo:</label>
            <select value={filtros.sexo || ''} onChange={(e) => setFilter('sexo', e.target.value || null)}>
              <option value="">Todos</option><option value="F">Femenino</option><option value="M">Masculino</option>
            </select>
            <label>Intencionalidad:</label>
            <select value={filtros.intencionalidad || ''} onChange={(e) => setFilter('intencionalidad', e.target.value || null)}>
              <option value="">Todas</option><option value="intencional">Intencional</option><option value="no_intencional">No intencional</option>
            </select>
            <label>Top N:</label>
            <select value={filtros.topN} onChange={(e) => setFiltros(prev => ({ ...prev, topN: e.target.value }))}>
              <option value="todas">Todas</option><option value="top5">Top 5</option><option value="top10">Top 10</option>
            </select>
          </div>
        </div>

        <section id="kpis">
          <div className="section-title">📊 KPIs Principales {hasActiveFilters && <span style={{ fontSize: '0.7rem', color: '#6366f1', fontWeight: 600 }}>(filtrados)</span>}</div>
          <div className="kpi-grid">
            <KpiCard icon="📋" label="Total Registros" value={kpis.total_registros.toLocaleString('es-CO')} />
            <KpiCard icon="✅" label="Intencionales" value={kpis.intencional.toLocaleString('es-CO')} sub={`${kpis.pct_intencional}%`} onClick={() => setFilter('intencionalidad', 'intencional')} active={filtros.intencionalidad === 'intencional'} />
            <KpiCard icon="⚠" label="No Intencionales" value={kpis.no_intencional.toLocaleString('es-CO')} sub={`${kpis.pct_no_intencional}%`} onClick={() => setFilter('intencionalidad', 'no_intencional')} active={filtros.intencionalidad === 'no_intencional'} />
            <KpiCard icon="🥇" label="Sustancia + Frecuente" value={kpis.sustancia_mas_frecuente} onClick={() => setFilter('sustancia', kpis.sustancia_mas_frecuente)} active={filtros.sustancia === kpis.sustancia_mas_frecuente} />
            <KpiCard icon="🥈" label="2ª Sustancia" value={kpis.segunda_sustancia} onClick={() => setFilter('sustancia', kpis.segunda_sustancia)} active={filtros.sustancia === kpis.segunda_sustancia} />
            <KpiCard icon="🥉" label="3ª Sustancia" value={kpis.tercera_sustancia} onClick={() => setFilter('sustancia', kpis.tercera_sustancia)} active={filtros.sustancia === kpis.tercera_sustancia} />
            <KpiCard icon="🎯" label="+ Intencional" value={sustanciaMasIntencional} onClick={() => setFilter('sustancia', sustanciaMasIntencional)} active={filtros.sustancia === sustanciaMasIntencional} />
            <KpiCard icon="♀" label="Sexo Femenino" value={kpis.sexo_f.toLocaleString('es-CO')} onClick={() => setFilter('sexo', 'F')} active={filtros.sexo === 'F'} />
            <KpiCard icon="♂" label="Sexo Masculino" value={kpis.sexo_m.toLocaleString('es-CO')} onClick={() => setFilter('sexo', 'M')} active={filtros.sexo === 'M'} />
            <KpiCard icon="🏷" label="Categorías" value={kpis.categorias_detectadas} />
          </div>
        </section>

        <section id="sustancias">
          <div className="section-title">🧪 Análisis por Tipo de Sustancia</div>
          <div className="card">
            <div className="card-title">📊 Conteo por Sustancia — clic en una barra para filtrar</div>
            <ResponsiveContainer width="100%" height={Math.max(300, filteredSustancias.length * 28)}>
              <BarChart data={filteredSustancias} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="sustancia" type="category" width={180} tick={{ fontSize: 11, fontWeight: 500 }} />
                <Tooltip formatter={(v) => v.toLocaleString('es-CO')} contentStyle={{ borderRadius: '0.5rem', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Legend />
                <Bar dataKey="numero_registros" name="Registros" fill="#6366f1" radius={[0, 6, 6, 0]} barSize={20}
                  onClick={(data) => setFilter('sustancia', data?.sustancia || data?.payload?.sustancia)}
                  style={{ cursor: 'pointer' }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section id="sexo">
          <div className="section-title">⚥ Análisis por Sexo</div>
          <div className="kpi-grid" style={{ marginBottom: '1rem' }}>
            <KpiCard icon="♀" label="Total Femenino" value={sexoTotales[0]?.numero_registros?.toLocaleString('es-CO')} sub={`${kpis.total_registros ? ((sexoTotales[0]?.numero_registros / kpis.total_registros) * 100).toFixed(1) : 0}%`} onClick={() => setFilter('sexo', 'F')} active={filtros.sexo === 'F'} />
            <KpiCard icon="♂" label="Total Masculino" value={sexoTotales[1]?.numero_registros?.toLocaleString('es-CO')} sub={`${kpis.total_registros ? ((sexoTotales[1]?.numero_registros / kpis.total_registros) * 100).toFixed(1) : 0}%`} onClick={() => setFilter('sexo', 'M')} active={filtros.sexo === 'M'} />
          </div>
          <div className="card">
            <div className="card-title">🥧 Distribución por Sexo — clic para filtrar</div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={sexoTotales} dataKey="numero_registros" nameKey="sexo" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  onClick={(data) => setFilter('sexo', data?.sexo || data?.name)} style={{ cursor: 'pointer' }}>
                  {sexoTotales.map((_, i) => (<Cell key={i} fill={sexoTotales[i]?.sexo === 'F' ? '#ec4899' : '#6366f1'} />))}
                </Pie>
                <Tooltip formatter={(v) => v.toLocaleString('es-CO')} /><Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <div className="card-title">📊 Sustancias por Sexo</div>
            <ResponsiveContainer width="100%" height={Math.max(350, sexoData.length * 26)}>
              <BarChart data={sexoData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" /><YAxis dataKey="sustancia" type="category" width={180} tick={{ fontSize: 11, fontWeight: 500 }} />
                <Tooltip formatter={(v) => v.toLocaleString('es-CO')} /><Legend />
                <Bar dataKey="F" name="Femenino" fill="#ec4899" radius={[0, 4, 4, 0]} barSize={16} />
                <Bar dataKey="M" name="Masculino" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section id="intencionalidad">
          <div className="section-title">🎯 Análisis por Intencionalidad</div>
          <div className="card">
            <div className="card-title">🥧 Distribución de Intencionalidad — clic para filtrar</div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={intencionalidadTotales} dataKey="numero_registros" nameKey="intencionalidad" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  onClick={(data) => setFilter('intencionalidad', data?.intencionalidad || data?.name || data?.payload?.intencionalidad)} style={{ cursor: 'pointer' }}>
                  {intencionalidadTotales.map((_, i) => (<Cell key={i} fill={intencionalidadTotales[i]?.intencionalidad === 'intencional' ? '#ef4444' : '#10b981'} />))}
                </Pie>
                <Tooltip formatter={(v) => v.toLocaleString('es-CO')} /><Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <div className="card-title">📊 Sustancias por Intencionalidad (Barras Apiladas)</div>
            <ResponsiveContainer width="100%" height={Math.max(350, intencionalidadData.length * 26)}>
              <BarChart data={intencionalidadData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" /><YAxis dataKey="sustancia" type="category" width={180} tick={{ fontSize: 11, fontWeight: 500 }} />
                <Tooltip formatter={(v) => v.toLocaleString('es-CO')} /><Legend />
                <Bar dataKey="intencional" name="Intencional" stackId="a" fill="#ef4444" barSize={20} />
                <Bar dataKey="no_intencional" name="No Intencional" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <div className="card-title">📋 Tabla de Intencionalidad por Sustancia</div>
            <DataTable data={intencionalidadData} columns={[
              { key: 'sustancia', label: 'Sustancia' }, { key: 'total', label: 'Total' },
              { key: 'intencional', label: 'Intencional' }, { key: 'no_intencional', label: 'No Intencional' },
              { key: 'porcentaje_intencional', label: '% Intencional' }, { key: 'porcentaje_no_intencional', label: '% No Intencional' },
            ]} exportFilename="intencionalidad_por_sustancia.csv" showFilters={false} />
          </div>
        </section>

        <section id="productos">
          <div className="section-title">📦 Análisis de Productos</div>
          <div className="card">
            <div className="card-title">🔍 Buscar Productos</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
              <input type="text" placeholder="🔍 Buscar producto..." value={prodSearch} onChange={(e) => setProdSearch(e.target.value)}
                style={{ padding: '0.5rem 0.85rem', borderRadius: '0.5rem', border: '1.5px solid #e2e8f0', minWidth: '200px', fontFamily: 'inherit', outline: 'none' }} />
              <select value={prodCategoria} onChange={(e) => setProdCategoria(e.target.value)} style={{ padding: '0.5rem 0.85rem', borderRadius: '0.5rem', border: '1.5px solid #e2e8f0', fontFamily: 'inherit', cursor: 'pointer' }}>
                <option value="__all__">Todas las categorías</option>
                {uniqueCategoriasProductos.map(c => (<option key={c} value={c}>{c}</option>))}
              </select>
              <select value={prodMetodo} onChange={(e) => setProdMetodo(e.target.value)} style={{ padding: '0.5rem 0.85rem', borderRadius: '0.5rem', border: '1.5px solid #e2e8f0', fontFamily: 'inherit', cursor: 'pointer' }}>
                <option value="__all__">Todos los métodos</option>
                <option value="deterministic">Deterministic</option><option value="llm">LLM</option><option value="cache">Cache</option><option value="blacklist">Blacklist</option><option value="default">Default</option>
              </select>
              <button className="btn btn-secondary" onClick={() => { setProdSearch(''); setProdCategoria('__all__'); setProdMetodo('__all__'); }}>Limpiar</button>
              <button className="btn btn-primary" onClick={() => {
                const h = ['categoria', 'producto', 'conteo', 'metodo_clasificacion'].join(',');
                const r = productosFiltrados.map(x => `"${x.categoria}","${x.producto}","${x.conteo}","${x.metodo_clasificacion}"`);
                const csv = [h, ...r].join('\n'); const b = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const l = document.createElement('a'); l.href = URL.createObjectURL(b); l.download = 'productos.csv'; l.click();
              }}>Exportar CSV</button>
            </div>
            <DataTable data={productosFiltrados} columns={[{ key: 'categoria', label: 'Categoría' }, { key: 'producto', label: 'Producto' }, { key: 'conteo', label: 'Conteo' }, { key: 'metodo_clasificacion', label: 'Método' }]} exportFilename="productos.csv" showFilters={false} showSearch={false} showExport={false} />
          </div>
        </section>

        <section id="tabla">
          <div className="section-title">🔍 Tabla Exploratoria de Resultados {hasActiveFilters && <span style={{ fontSize: '0.7rem', color: '#6366f1', fontWeight: 600 }}>(filtrada)</span>}</div>
          <div className="card">
            <div className="card-title">Resultados de Clasificación Avanzada</div>
            <DataTable data={resultadosLlmFiltrados} columns={[
              { key: 'origen_hoja', label: 'Origen' }, { key: 'fec_not', label: 'Fecha' }, { key: 'sexo', label: 'Sexo' }, { key: 'edad', label: 'Edad' },
              { key: 'nom_pro', label: 'Producto' }, { key: 'grupos_sustancia_final', label: 'Sustancia Final' }, { key: 'metodo_clasificacion', label: 'Método' },
            ]} filterOptions={{ sexo: ['F', 'M'], metodo_clasificacion: uniqueMetodos, origen_hoja: uniqueOrigenes.slice(0, 20) }} exportFilename="resultados_clasificacion.csv" />
          </div>
          <div className="card" style={{ marginTop: '1.25rem' }}>
            <div className="card-title">Base Completa (con Intencionalidad)</div>
            <DataTable data={filteredBase} columns={[
              { key: 'origen_hoja', label: 'Origen' }, { key: 'fec_not', label: 'Fecha' }, { key: 'sexo', label: 'Sexo' }, { key: 'edad', label: 'Edad' },
              { key: 'nom_pro', label: 'Producto' }, { key: 'grupos_sustancia_final', label: 'Sustancia' }, { key: 'intencionalidad', label: 'Intencionalidad' }, { key: 'metodo_clasificacion', label: 'Método' },
            ]} filterOptions={{ sexo: ['F', 'M'], intencionalidad: ['intencional', 'no_intencional'] }} exportFilename="base_completa.csv" />
          </div>
        </section>

        <section id="hallazgos">
          <div className="section-title">💡 Hallazgos Principales</div>
          <div className="findings-box"><h4>📋 Resumen</h4><p>El análisis abarca <strong>{kpis.total_registros.toLocaleString('es-CO')} registros</strong> en <strong>{kpis.categorias_detectadas} categorías</strong>. La más frecuente es <strong>{kpis.sustancia_mas_frecuente}</strong>, seguida de <strong>{kpis.segunda_sustancia}</strong> y <strong>{kpis.tercera_sustancia}</strong>.</p></div>
          <div className="findings-box"><h4>⚥ Por Sexo</h4><ul><li>Femenino: <strong>{kpis.sexo_f?.toLocaleString('es-CO')}</strong> registros ({kpis.total_registros ? ((kpis.sexo_f / kpis.total_registros) * 100).toFixed(1) : 0}%)</li><li>Masculino: <strong>{kpis.sexo_m?.toLocaleString('es-CO')}</strong> registros ({kpis.total_registros ? ((kpis.sexo_m / kpis.total_registros) * 100).toFixed(1) : 0}%)</li><li>Las mujeres predominan en medicamentos_no_SPA y tranquilizantes; los hombres en alcohol, cocaína y cannabinoides.</li></ul></div>
          <div className="findings-box"><h4>🎯 Por Intencionalidad</h4><ul><li><strong>{kpis.intencional?.toLocaleString('es-CO')}</strong> intencionales ({kpis.pct_intencional}%)</li><li><strong>{kpis.no_intencional?.toLocaleString('es-CO')}</strong> no intencionales ({kpis.pct_no_intencional}%)</li><li>Sustancia más asociada a intencionalidad: <strong>{sustanciaMasIntencional}</strong>.</li></ul></div>
          <div className="findings-box"><h4>📏 Limitaciones</h4><ul><li>La categoría "otros" concentra mucho volumen y puede enmascarar patrones.</li><li>Datos de notificación epidemiológica, sujetos a sesgos de reporte.</li><li>Algunos registros pertenecen a múltiples categorías.</li></ul></div>
        </section>

        <section id="originales">
          <div className="section-title">🖼 Gráficas Originales Generadas por la Corrida</div>
          <div className="gallery-grid">
            {originalImages.map((img, idx) => (<div className="gallery-card" key={idx}><img src={img.src} alt={img.title} loading="lazy" /><div className="caption"><h4>{img.title}</h4><p>{img.desc}</p></div></div>))}
          </div>
        </section>

        <footer className="dashboard-footer">Dashboard generado automáticamente desde outputs/clasificaciones_conteo · {fechaGeneracion}</footer>
      </main>
      <ChatBot />
    </div>
  );
};

export default App;
