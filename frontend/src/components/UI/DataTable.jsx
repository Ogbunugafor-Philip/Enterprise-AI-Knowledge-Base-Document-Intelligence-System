import React, { useState, useMemo } from 'react';
import { Search, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';

function SkeletonRow({ cols }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
        </td>
      ))}
    </tr>
  );
}

export default function DataTable({
  columns = [], data = [], loading = false,
  emptyMessage = 'No records found', pageSize = 10,
  searchable = true, actions, rowKey = 'id',
}) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const filtered = useMemo(() => {
    if (!search.trim()) return data;
    const q = search.toLowerCase();
    return data.filter(row =>
      columns.some(col => {
        const val = col.accessor ? (typeof col.accessor === 'function' ? col.accessor(row) : row[col.accessor]) : '';
        return String(val ?? '').toLowerCase().includes(q);
      })
    );
  }, [data, search, columns]);

  const sorted = useMemo(() => {
    if (!sortCol) return filtered;
    return [...filtered].sort((a, b) => {
      const col = columns.find(c => c.key === sortCol);
      const va = col?.accessor ? (typeof col.accessor === 'function' ? col.accessor(a) : a[col.accessor]) : '';
      const vb = col?.accessor ? (typeof col.accessor === 'function' ? col.accessor(b) : b[col.accessor]) : '';
      const cmp = String(va ?? '').localeCompare(String(vb ?? ''));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortCol, sortDir, columns]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const paged = sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  function toggleSort(key) {
    if (sortCol === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortCol(key); setSortDir('asc'); }
  }

  return (
    <div className="table-container">
      {(searchable || actions) && (
        <div className="flex items-center justify-between gap-4 px-6 py-4 border-b border-gray-100">
          {searchable && (
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                className="input pl-9 bg-gray-50 border-gray-200"
                placeholder="Search…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
          )}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key || col.header} className={col.sortable ? 'cursor-pointer select-none' : ''} onClick={() => col.sortable && toggleSort(col.key)}>
                  <div className="flex items-center gap-1">
                    {col.header}
                    {col.sortable && <ArrowUpDown className="w-3 h-3 text-gray-400" />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} cols={columns.length} />)
              : paged.length === 0
              ? (
                <tr>
                  <td colSpan={columns.length} className="empty-state">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-2xl">📋</div>
                      <p className="font-medium text-gray-500">{emptyMessage}</p>
                    </div>
                  </td>
                </tr>
              )
              : paged.map((row, idx) => (
                <tr key={row[rowKey] || idx}>
                  {columns.map(col => (
                    <td key={col.key || col.header}>
                      {col.render ? col.render(row) : (col.accessor ? (typeof col.accessor === 'function' ? col.accessor(row) : row[col.accessor]) : '')}
                    </td>
                  ))}
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
      {!loading && sorted.length > pageSize && (
        <div className="flex items-center justify-between px-6 py-3 border-t border-gray-100 text-sm text-gray-500">
          <span>Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, sorted.length)} of {sorted.length}</span>
          <div className="flex items-center gap-1">
            <button className="btn-secondary px-2 py-1.5 text-xs" disabled={currentPage === 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 font-medium text-gray-700">{currentPage} / {totalPages}</span>
            <button className="btn-secondary px-2 py-1.5 text-xs" disabled={currentPage === totalPages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
