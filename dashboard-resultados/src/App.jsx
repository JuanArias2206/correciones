import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import KpiCard from './components/KpiCard';
import DataTable from './components/DataTable';
import {
  kpis, sustancias, intencionalidad, sexo, sustanciasPorIntencionalidad,
  sustanciaSexo, productosTodos, conteoCategorias, resultadosLlm,
  resumenCategorias, baseCompleta, metadata
} from './data/data';

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#14b8a6', '#d946ef'];

const sections = [
  { id: 'kpis', label: 'KPIs' },
  { id: 'sustancias', label: 'Por Sustancia' },
  { id: 'sexo', label: 'Por Sexo' },
  { id: 'intencionalidad', label: 'Por Intencionalidad' },
  { id: 'productos', label: 'Productos' },
  { id: 'tabla', label: 'Tabla Exploratoria' },
  { id: 'hallazgos', label: 'Hallazgos' },
  { id: 'originales', label: 'Gráficas Originales' },
];

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('kpis');

  // Filtros globales
  const [filterSustancia, setFilterSustancia] = useState('');
  const [filterSexo, setFilterSexo] = useState('');
  const [filterIntencionalidad, setFilterIntencionalidad] = useState('');
  const [topN, setTopN] = useState('todas');

  const scrollTo = (id) => {
    setActiveSection(id);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setSidebarOpen(false);
  };

  const fechaGeneracion = metadata?.fecha_generacion
    ? new Date(metadata.fecha_generacion).toLocaleString('es-CO')
    : new Date().toLocaleString('es-CO');

  // KPIs
  const totalRegistros = kpis.total_registros || 0;
  const intencionalTotal = kpis.intencional || 0;
  const noIntencionalTotal = kpis.no_intencional || 0;
  const pctInt = kpis.pct_intencional || 0;
  const pctNoInt = kpis.pct_no_intencional || 0;

  // Filtrar sustancias según filtros globales
  const filteredSustancias = useMemo(() => {
    let data = [...sustancias];
    if (filterSustancia) data = data.filter((d) => d.sustancia === filterSustancia);
    if (topN === 'top5') data = data.slice(0, 5);
    else if (topN === 'top10') data = data.slice(0, 10);
    return data;
  }, [filterSustancia, topN]);

  // Datos para intencionalidad
  const intencionalidadData = useMemo(() => {
    return sustanciasPorIntencionalidad.map((d) => ({
      sustancia: d.sustancia,
      intencional: Number(d.intencional) || 0,
      no_intencional: Number(d.no_intencional) || 0,
      total: Number(d.total) || 0,
      porcentaje_intencional: Number(d.porcentaje_intencional) || 0,
      porcentaje_no_intencional: Number(d.porcentaje_no_intencional) || 0,
    }));
  }, []);

  const intencionalidadFiltrada = useMemo(() => {
    let data = [...intencionalidadData];
    if (filterSustancia) data = data.filter((d) => d.sustancia === filterSustancia);
    if (filterIntencionalidad) {
      if (filterIntencionalidad === 'intencional') data = data.filter((d) => d.porcentaje_intencional > 50);
      else if (filterIntencionalidad === 'no_intencional') data = data.filter((d) => d.porcentaje_no_intencional > 50);
    }
    return data;
  }, [intencionalidadData, filterSustancia, filterIntencionalidad]);

  // Datos para sexo
  const sexoData = useMemo(() => {
    return sustanciaSexo.map((d) => ({
      sustancia: d.sustancia || d.grupos_sustancia_final,
      F: Number(d.F) || 0,
      M: Number(d.M) || 0,
      total: (Number(d.F) || 0) + (Number(d.M) || 0),
    }));
  }, []);

  const sexoFiltrado = useMemo(() => {
    let data = [...sexoData];
    if (filterSustancia) data = data.filter((d) => d.sustancia === filterSustancia);
    if (filterSexo) data = data.filter((d) => d[filterSexo] > 0);
    return data;
  }, [sexoData, filterSustancia, filterSexo]);

  // Lista única de sustancias para selectores
  const uniqueSustancias = useMemo(() => {
    return [...new Set(sustancias.map((s) => s.sustancia))];
  }, []);

  // Categorías de productos
  const uniqueCategoriasProductos = useMemo(() => {
    return [...new Set(productosTodos.map((p) => p.categoria))].sort();
  }, []);

  // Tabla de productos - filtros locales
  const [prodSearch, setProdSearch] = useState('');
  const [prodCategoria, setProdCategoria] = useState('__all__');
  const [prodMetodo, setProdMetodo] = useState('__all__');

  const productosFiltrados = useMemo(() => {
    let data = [...productosTodos];
    if (prodSearch.trim()) {
      const term = prodSearch.toLowerCase();
      data = data.filter((d) => String(d.producto).toLowerCase().includes(term));
    }
    if (prodCategoria !== '__all__') data = data.filter((d) => d.categoria === prodCategoria);
    if (prodMetodo !== '__all__') data = data.filter((d) => d.metodo_clasificacion === prodMetodo);
    return data;
  }, [prodSearch, prodCategoria, prodMetodo]);

  // Tabla exploratoria (resultados LLM)
  const uniqueMetodos = useMemo(() => [...new Set(resultadosLlm.map((r) => r.metodo_clasificacion).filter(Boolean))].sort(), []);
  const uniqueOrigenes = useMemo(() => [...new Set(resultadosLlm.map((r) => r.origen_hoja).filter(Boolean))].sort(), []);

  // Hallazgos calculados
  const sustanciaTop1 = sustancias[0]?.sustancia || '';
  const sustanciaTop2 = sustancias[1]?.sustancia || '';
  const sustanciaTop3 = sustancias[2]?.sustancia || '';

  const sexoF_total = sexo.find((s) => s.sexo === 'F')?.numero_registros || 0;
  const sexoM_total = sexo.find((s) => s.sexo === 'M')?.numero_registros || 0;
  const pctF = totalRegistros ? ((sexoF_total / totalRegistros) * 100).toFixed(1) : 0;
  const pctM = totalRegistros ? ((sexoM_total / totalRegistros) * 100).toFixed(1) : 0;

  // Imágenes originales
  const originalImages = [
    { src: '/images/sustancias.png', title: 'Sustancias', desc: 'Conteo general de sustancias identificadas.' },
    { src: '/images/top10_sustancias.png', title: 'Top 10 Sustancias', desc: 'Las 10 sustancias más frecuentes.' },
    { src: '/images/conteo_sustancias_tipo.png', title: 'Conteo por Tipo', desc: 'Distribución por tipo de sustancia.' },
    { src: '/images/sexo.png', title: 'Sexo', desc: 'Distribución total por sexo.' },
    { src: '/images/sustancias_por_sexo.png', title: 'Sustancias por Sexo', desc: 'Comparación de sustancias entre sexos.' },
    { src: '/images/heatmap_sustancia_sexo.png', title: 'Heatmap Sustancia × Sexo', desc: 'Mapa de calor de sustancias por sexo.' },
    { src: '/images/intencionalidad.png', title: 'Intencionalidad', desc: 'Distribución general de intencionalidad.' },
    { src: '/images/sustancias_por_intencionalidad.png', title: 'Sustancias por Intencionalidad', desc: 'Comparación intencional vs no intencional.' },
  ];

  return (
    <div className="dashboard-container">
      <button className="mobile-menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
        ☰
      </button>

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-title">Dashboard</div>
        <ul className="sidebar-nav">
          {sections.map((s) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                className={activeSection === s.id ? 'active' : ''}
                onClick={(e) => { e.preventDefault(); scrollTo(s.id); }}
              >
                {s.label}
              </a>
            </li>
          ))}
        </ul>
      </aside>

      <main className="main-content">
        <div className="header-section">
          <h1>Dashboard de Análisis de Clasificación de Sustancias</h1>
          <p>Este tablero resume los resultados de clasificación, distribución por sustancia, sexo e intencionalidad de los registros procesados.</p>
          <div className="header-date">Última actualización: {fechaGeneracion}</div>
        </div>

        {/* Filtros globales */}
        <div className="card">
          <div className="card-title">Filtros Globales</div>
          <div className="filters-bar">
            <label>Sustancia:</label>
            <select value={filterSustancia} onChange={(e) => setFilterSustancia(e.target.value)}>
              <option value="">Todas</option>
              {uniqueSustancias.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            <label>Sexo:</label>
            <select value={filterSexo} onChange={(e) => setFilterSexo(e.target.value)}>
              <option value="">Todos</option>
              <option value="F">Femenino</option>
              <option value="M">Masculino</option>
            </select>

            <label>Intencionalidad:</label>
            <select value={filterIntencionalidad} onChange={(e) => setFilterIntencionalidad(e.target.value)}>
              <option value="">Todas</option>
              <option value="intencional">Predomina Intencional</option>
              <option value="no_intencional">Predomina No Intencional</option>
            </select>

            <label>Top N:</label>
            <select value={topN} onChange={(e) => setTopN(e.target.value)}>
              <option value="todas">Todas</option>
              <option value="top5">Top 5</option>
              <option value="top10">Top 10</option>
            </select>
          </div>
        </div>

        {/* KPIs */}
        <section id="kpis">
          <div className="section-title">KPIs Principales</div>
          <div className="kpi-grid">
            <KpiCard label="Total Registros" value={totalRegistros.toLocaleString('es-CO')} />
            <KpiCard label="Intencionales" value={intencionalTotal.toLocaleString('es-CO')} sub={`${pctInt}%`} />
            <KpiCard label="No Intencionales" value={noIntencionalTotal.toLocaleString('es-CO')} sub={`${pctNoInt}%`} />
            <KpiCard label="Sustancia + Frecuente" value={kpis.sustancia_mas_frecuente || '-'} />
            <KpiCard label="2da Sustancia" value={kpis.segunda_sustancia || '-'} />
            <KpiCard label="3ra Sustancia" value={kpis.tercera_sustancia || '-'} />
            <KpiCard label="Sustancia + Intencional" value={kpis.sustancia_mas_intencional || '-'} />
            <KpiCard label="Sexo F" value={(kpis.sexo_f || 0).toLocaleString('es-CO')} />
            <KpiCard label="Sexo M" value={(kpis.sexo_m || 0).toLocaleString('es-CO')} />
            <KpiCard label="Categorías Detectadas" value={kpis.categorias_detectadas || 0} />
          </div>
        </section>

        {/* Análisis por Sustancia */}
        <section id="sustancias">
          <div className="section-title">Análisis por Tipo de Sustancia</div>
          <div className="card">
            <div className="card-title">Conteo por Tipo de Sustancia</div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={filteredSustancias} layout="vertical" margin={{ left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="sustancia" type="category" width={180} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Legend />
                <Bar dataKey="numero_registros" name="Registros" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-title">Top Categorías (Resumen)</div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resumenCategorias.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="Clasificación Final" tick={{ fontSize: 12 }} interval={0} angle={-25} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Bar dataKey="Conteo" name="Conteo" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Análisis por Sexo */}
        <section id="sexo">
          <div className="section-title">Análisis por Sexo</div>
          <div className="kpi-grid" style={{ marginBottom: '1rem' }}>
            <KpiCard label="Total Femenino" value={sexoF_total.toLocaleString('es-CO')} sub={`${pctF}% del total`} />
            <KpiCard label="Total Masculino" value={sexoM_total.toLocaleString('es-CO')} sub={`${pctM}% del total`} />
          </div>

          <div className="card">
            <div className="card-title">Distribución por Sexo</div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sexo}
                  dataKey="numero_registros"
                  nameKey="sexo"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                >
                  {sexo.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.sexo === 'F' ? '#ec4899' : '#2563eb'} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-title">Sustancias por Sexo (Barras Agrupadas)</div>
            <ResponsiveContainer width="100%" height={450}>
              <BarChart data={sexoFiltrado} layout="vertical" margin={{ left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="sustancia" type="category" width={180} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Legend />
                <Bar dataKey="F" name="Femenino" fill="#ec4899" />
                <Bar dataKey="M" name="Masculino" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="text-analysis">
            <h4 style={{ marginBottom: '0.75rem', color: '#1e40af' }}>Interpretación por Sexo</h4>
            <p>
              El análisis muestra una <strong>mayor volumetría general en el sexo femenino</strong> ({sexoF_total.toLocaleString('es-CO')} registros, {pctF}%),
              especialmente en categorías como <strong>medicamentos_no_SPA</strong>, <strong>tranquilizantes_y_sedantes</strong> y <strong>otros</strong>.
            </p>
            <p>
              Sin embargo, se observa una <strong>mayor presencia masculina relativa</strong> en <strong>alcohol_etanol</strong>,
              <strong> cocaína_y_derivados</strong> y <strong>cannabinoides</strong>, lo cual sugiere patrones diferenciados de consumo o exposición por género.
            </p>
          </div>
        </section>

        {/* Análisis por Intencionalidad */}
        <section id="intencionalidad">
          <div className="section-title">Análisis por Intencionalidad</div>
          <div className="card">
            <div className="card-title">Distribución General de Intencionalidad</div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={intencionalidad}
                  dataKey="numero_registros"
                  nameKey="intencionalidad"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                >
                  {intencionalidad.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.intencionalidad === 'intencional' ? '#ef4444' : '#10b981'} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-title">Sustancias por Intencionalidad (Barras Apiladas)</div>
            <ResponsiveContainer width="100%" height={450}>
              <BarChart data={intencionalidadFiltrada} layout="vertical" margin={{ left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="sustancia" type="category" width={180} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Legend />
                <Bar dataKey="intencional" name="Intencional" stackId="a" fill="#ef4444" />
                <Bar dataKey="no_intencional" name="No Intencional" stackId="a" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-title">Tabla de Intencionalidad por Sustancia</div>
            <DataTable
              data={intencionalidadFiltrada}
              columns={[
                { key: 'sustancia', label: 'Sustancia' },
                { key: 'total', label: 'Total' },
                { key: 'intencional', label: 'Intencional' },
                { key: 'no_intencional', label: 'No Intencional' },
                { key: 'porcentaje_intencional', label: '% Intencional' },
                { key: 'porcentaje_no_intencional', label: '% No Intencional' },
              ]}
              exportFilename="intencionalidad_por_sustancia.csv"
              showFilters={false}
            />
          </div>

          <div className="text-analysis">
            <h4 style={{ marginBottom: '0.75rem', color: '#1e40af' }}>Interpretación por Intencionalidad</h4>
            <p>
              Las categorías con <strong>mayor volumen absoluto</strong> son <strong>otros</strong>, <strong>medicamentos_no_SPA</strong> y <strong>tranquilizantes_y_sedantes</strong>.
            </p>
            <p>
              En varias categorías, los registros <strong>no intencionales superan a los intencionales</strong>, lo cual es importante considerar al interpretar los resultados globales.
              Las categorías de mayor volumen deben tratarse con cuidado porque pueden dominar el análisis agregado.
            </p>
          </div>
        </section>

        {/* Productos */}
        <section id="productos">
          <div className="section-title">Análisis de Productos</div>
          <div className="card">
            <div className="card-title">Conteo de Productos por Categoría</div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={conteoCategorias}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="categoria" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip formatter={(value) => value.toLocaleString('es-CO')} />
                <Bar dataKey="conteo" name="Productos" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-title">Tabla de Productos</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
              <input
                type="text"
                placeholder="Buscar producto..."
                value={prodSearch}
                onChange={(e) => setProdSearch(e.target.value)}
                style={{ padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid #d1d5db', minWidth: '200px' }}
              />
              <select value={prodCategoria} onChange={(e) => setProdCategoria(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid #d1d5db' }}>
                <option value="__all__">Todas las categorías</option>
                {uniqueCategoriasProductos.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select value={prodMetodo} onChange={(e) => setProdMetodo(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.5rem', border: '1px solid #d1d5db' }}>
                <option value="__all__">Todos los métodos</option>
                <option value="deterministic">Deterministic</option>
                <option value="llm">LLM</option>
                <option value="cache">Cache</option>
                <option value="blacklist">Blacklist</option>
                <option value="default">Default</option>
              </select>
              <button className="btn btn-secondary" onClick={() => { setProdSearch(''); setProdCategoria('__all__'); setProdMetodo('__all__'); }}>
                Limpiar
              </button>
              <button className="btn btn-primary" onClick={() => {
                const headers = ['categoria', 'producto', 'conteo', 'metodo_clasificacion'].join(',');
                const rows = productosFiltrados.map((r) => `"${r.categoria}","${r.producto}","${r.conteo}","${r.metodo_clasificacion}"`);
                const csv = [headers, ...rows].join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'productos_filtrados.csv';
                link.click();
              }}>
                Exportar CSV
              </button>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '0.5rem' }}>
              Mostrando {productosFiltrados.length} productos
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Categoría</th>
                    <th>Producto</th>
                    <th>Conteo</th>
                    <th>Método</th>
                  </tr>
                </thead>
                <tbody>
                  {productosFiltrados.slice(0, 100).map((p, i) => (
                    <tr key={i}>
                      <td>{p.categoria}</td>
                      <td>{p.producto}</td>
                      <td>{p.conteo}</td>
                      <td>{p.metodo_clasificacion}</td>
                    </tr>
                  ))}
                  {productosFiltrados.length === 0 && (
                    <tr><td colSpan={4} style={{ textAlign: 'center', padding: '2rem' }}>No hay productos</td></tr>
                  )}
                </tbody>
              </table>
              {productosFiltrados.length > 100 && (
                <div style={{ textAlign: 'center', padding: '1rem', fontSize: '0.85rem', color: '#6b7280' }}>
                  Mostrando primeros 100 de {productosFiltrados.length} productos. Use los filtros o exporte CSV para ver todos.
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Tabla Exploratoria */}
        <section id="tabla">
          <div className="section-title">Tabla Exploratoria de Resultados</div>
          <div className="card">
            <div className="card-title">Resultados de Clasificación Avanzada</div>
            <DataTable
              data={resultadosLlm}
              columns={[
                { key: 'origen_hoja', label: 'Origen' },
                { key: 'fec_not', label: 'Fecha Notificación' },
                { key: 'sexo', label: 'Sexo' },
                { key: 'edad', label: 'Edad' },
                { key: 'nom_pro', label: 'Producto' },
                { key: 'grupos_sustancia_final', label: 'Sustancia Final' },
                { key: 'metodo_clasificacion', label: 'Método' },
              ]}
              filterOptions={{
                sexo: ['F', 'M'],
                metodo_clasificacion: uniqueMetodos,
                origen_hoja: uniqueOrigenes.slice(0, 20),
              }}
              exportFilename="resultados_clasificacion.csv"
            />
          </div>

          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="card-title">Base Completa (Registros con Intencionalidad)</div>
            <DataTable
              data={baseCompleta}
              columns={[
                { key: 'origen_hoja', label: 'Origen' },
                { key: 'fec_not', label: 'Fecha' },
                { key: 'sexo', label: 'Sexo' },
                { key: 'edad', label: 'Edad' },
                { key: 'nom_pro', label: 'Producto' },
                { key: 'grupos_sustancia_final', label: 'Sustancia' },
                { key: 'intencionalidad', label: 'Intencionalidad' },
                { key: 'metodo_clasificacion', label: 'Método' },
              ]}
              filterOptions={{
                sexo: ['F', 'M'],
                intencionalidad: ['intencional', 'no_intencional'],
              }}
              exportFilename="base_completa.csv"
            />
          </div>
        </section>

        {/* Hallazgos */}
        <section id="hallazgos">
          <div className="section-title">Hallazgos Principales</div>
          <div className="findings-box">
            <h4>Resumen Ejecutivo</h4>
            <p>
              El análisis abarca <strong>{totalRegistros.toLocaleString('es-CO')} registros</strong> clasificados en <strong>{kpis.categorias_detectadas || 0} categorías</strong> de sustancias.
              La categoría más frecuente es <strong>{sustanciaTop1}</strong>, seguida de <strong>{sustanciaTop2}</strong> y <strong>{sustanciaTop3}</strong>.
            </p>
          </div>

          <div className="findings-box">
            <h4>Diferencias por Sexo</h4>
            <ul>
              <li>El sexo femenino concentra el {pctF}% de los registros totales ({sexoF_total.toLocaleString('es-CO')} casos).</li>
              <li>Las mujeres presentan mayor frecuencia en medicamentos_no_SPA, tranquilizantes_y_sedantes y la categoría "otros".</li>
              <li>Los hombres tienen mayor representación proporcional en alcohol_etanol, cocaína_y_derivados y cannabinoides.</li>
              <li>Estas diferencias pueden reflejar patrones de uso, acceso o reporte diferenciados por género.</li>
            </ul>
          </div>

          <div className="findings-box">
            <h4>Diferencias por Intencionalidad</h4>
            <ul>
              <li>El {pctInt}% de los registros son intencionales ({intencionalTotal.toLocaleString('es-CO')} casos).</li>
              <li>El {pctNoInt}% son no intencionales ({noIntencionalTotal.toLocaleString('es-CO')} casos).</li>
              <li>En varias categorías predominan los registros no intencionales, lo cual sugiere exposiciones accidentales o involuntarias.</li>
              <li>La sustancia más asociada a intencionalidad es <strong>{kpis.sustancia_mas_intencional || 'N/A'}</strong>.</li>
            </ul>
          </div>

          <div className="findings-box">
            <h4>Categorías con Mayor Concentración</h4>
            <ul>
              <li><strong>otros</strong>: categoría residual con el mayor volumen, que incluye productos no clasificados o de difícil categorización.</li>
              <li><strong>medicamentos_no_SPA</strong>: segunda categoría más frecuente, dominada por registros femeninos.</li>
              <li><strong>tranquilizantes_y_sedantes</strong>: tercera en frecuencia, también con predominio femenino.</li>
            </ul>
          </div>

          <div className="findings-box">
            <h4>Alertas y Patrones Importantes</h4>
            <ul>
              <li>La alta proporción de la categoría "otros" puede indicar necesidad de refinamiento en la clasificación.</li>
              <li>La categoría medicamentos_no_SPA + tranquilizantes_y_sedantes representa un gran volumen de exposiciones a psicofármacos.</li>
              <li>El uso de múltiples métodos de clasificación (deterministic, LLM, cache, blacklist) indica un proceso híbrido que debe validarse.</li>
            </ul>
          </div>

          <div className="findings-box">
            <h4>Limitaciones del Análisis</h4>
            <ul>
              <li>La categoría "otros" concentra un volumen muy grande que puede enmascarar patrones específicos.</li>
              <li>Los datos provienen de notificación epidemiológica y pueden tener sesgos de reporte.</li>
              <li>Algunos registros pueden pertenecer a múltiples categorías (listas en grupos_sustancia_filtrado).</li>
              <li>La intencionalidad puede ser difícil de determinar en contextos clínicos o de emergencias.</li>
            </ul>
          </div>
        </section>

        {/* Gráficas originales */}
        <section id="originales">
          <div className="section-title">Gráficas Originales Generadas por la Corrida</div>
          <div className="gallery-grid">
            {originalImages.map((img, idx) => (
              <div className="gallery-card" key={idx}>
                <img src={img.src} alt={img.title} loading="lazy" />
                <div className="caption">
                  <h4>{img.title}</h4>
                  <p>{img.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <footer style={{ marginTop: '3rem', padding: '1.5rem', textAlign: 'center', color: '#6b7280', fontSize: '0.875rem', borderTop: '1px solid #e5e7eb' }}>
          Dashboard generado automáticamente desde la carpeta outputs/clasificaciones_conteo · {fechaGeneracion}
        </footer>
      </main>
    </div>
  );
};

export default App;
