import React, { useState, useMemo } from 'react';

const DataTable = ({
  data,
  columns,
  searchPlaceholder = 'Buscar...',
  pageSizeOptions = [10, 25, 50, 100],
  defaultPageSize = 25,
  filterOptions = {},
  exportFilename = 'datos.csv',
  showSearch = true,
  showFilters = true,
  showPagination = true,
  showExport = true,
  extraFilters = null,
}) => {
  const [search, setSearch] = useState('');
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  const [filters, setFilters] = useState({});

  const handleSort = (key) => {
    if (sortColumn === key) {
      // Ciclo: asc -> desc -> sin orden
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else {
        setSortColumn(null);
        setSortDirection('asc');
      }
    } else {
      setSortColumn(key);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setSearch('');
    setSortColumn(null);
    setSortDirection('asc');
    setCurrentPage(1);
  };

  const filteredData = useMemo(() => {
    let result = [...data];

    if (search.trim()) {
      const term = search.toLowerCase();
      result = result.filter((row) =>
        columns.some((col) => {
          const val = row[col.key];
          if (val == null) return false;
          return String(val).toLowerCase().includes(term);
        })
      );
    }

    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== '__all__') {
        result = result.filter((row) => String(row[key]) === String(value));
      }
    });

    if (sortColumn) {
      result.sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        }
        const aStr = String(aVal).toLowerCase();
        const bStr = String(bVal).toLowerCase();
        if (aStr < bStr) return sortDirection === 'asc' ? -1 : 1;
        if (aStr > bStr) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [data, search, filters, sortColumn, sortDirection, columns]);

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedData = filteredData.slice(startIndex, startIndex + pageSize);

  const exportCSV = () => {
    const headers = columns.map((c) => c.label).join(',');
    const rows = filteredData.map((row) =>
      columns
        .map((c) => {
          const val = row[c.key];
          const str = val == null ? '' : String(val).replace(/"/g, '""');
          return `"${str}"`;
        })
        .join(',')
    );
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = exportFilename;
    link.click();
  };

  const getSortIcon = (key) => {
    if (sortColumn !== key) {
      return (
        <span style={{ color: '#d1d5db', fontSize: '0.75rem', marginLeft: '0.25rem' }} title="Click para ordenar ascendente">
          ⇅
        </span>
      );
    }
    return sortDirection === 'asc' ? (
      <span style={{ color: '#2563eb', fontSize: '0.85rem', marginLeft: '0.25rem', fontWeight: 700 }} title="Orden ascendente. Click para descendente">
        ▲
      </span>
    ) : (
      <span style={{ color: '#2563eb', fontSize: '0.85rem', marginLeft: '0.25rem', fontWeight: 700 }} title="Orden descendente. Click para quitar orden">
        ▼
      </span>
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        {showSearch && (
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
            style={{ padding: '0.5rem 0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', minWidth: '200px' }}
          />
        )}
        {showFilters && Object.entries(filterOptions).map(([key, options]) => (
          <select
            key={key}
            value={filters[key] || '__all__'}
            onChange={(e) => handleFilterChange(key, e.target.value)}
            style={{ padding: '0.5rem 0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem' }}
          >
            <option value="__all__">{key}</option>
            {options.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        ))}
        {extraFilters}
        <button className="btn btn-secondary" onClick={clearFilters}>Limpiar filtros</button>
        {showExport && (
          <button className="btn btn-primary" onClick={exportCSV}>Exportar CSV</button>
        )}
      </div>

      <div style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '0.5rem' }}>
        Mostrando {filteredData.length} registros
        {sortColumn && (
          <span style={{ marginLeft: '0.5rem', fontWeight: 600, color: '#2563eb' }}>
            · Ordenado por "{columns.find(c => c.key === sortColumn)?.label || sortColumn}" ({sortDirection === 'asc' ? 'ascendente' : 'descendente'})
          </span>
        )}
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap' }}
                >
                  {col.label} {getSortIcon(col.key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col.key}>{row[col.key] != null ? String(row[col.key]) : ''}</td>
                ))}
              </tr>
            ))}
            {paginatedData.length === 0 && (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: '2rem' }}>
                  No hay registros para mostrar.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showPagination && (
        <div className="pagination">
          <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1}>«</button>
          <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1}>‹</button>
          <span style={{ fontSize: '0.875rem', color: '#374151' }}>
            Página {currentPage} de {totalPages}
          </span>
          <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>›</button>
          <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages}>»</button>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
            style={{ padding: '0.4rem', borderRadius: '0.375rem', border: '1px solid #d1d5db' }}
          >
            {pageSizeOptions.map((s) => (
              <option key={s} value={s}>{s} / pág</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};

export default DataTable;
