import { useState } from 'react';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  FileText, 
  X,
  Sparkles,
  ExternalLink,
  ShieldAlert,
  MapPin,
  User,
  Filter
} from 'lucide-react';

export default function InvestigationQueue({
  anomalies,
  loading,
  filters,
  search,
  setSearch,
  stateFilter,
  setStateFilter,
  constituencyFilter,
  setConstituencyFilter,
  mpFilter,
  setMpFilter,
  riskFilter,
  setRiskFilter,
  priorityFilter,
  setPriorityFilter,
  agreementFilter,
  setAgreementFilter,
  onClearFilters,
  onOpenWork,
  pagination,
  onPageChange
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const totalPages = Math.max(1, Math.ceil((pagination.total || 0) / (pagination.limit || 50)));
  const currentPage = Math.floor((pagination.offset || 0) / (pagination.limit || 50)) + 1;

  const isFiltered = Boolean(
    (search && search.trim()) ||
    (stateFilter && stateFilter !== 'ALL') ||
    (constituencyFilter && constituencyFilter !== 'ALL') ||
    (mpFilter && mpFilter !== 'ALL') ||
    (riskFilter && riskFilter !== 'ALL') ||
    (priorityFilter && priorityFilter !== 'ALL') ||
    (agreementFilter && agreementFilter !== 'ALL')
  );

  const getRiskClass = (level) => {
    const l = String(level || 'LOW').toUpperCase();
    if (l === 'CRITICAL') return 'high';
    if (l === 'HIGH') return 'high';
    if (l === 'MEDIUM') return 'medium';
    return 'low';
  };

  const getRiskColor = (level) => {
    const l = String(level || 'LOW').toUpperCase();
    if (l === 'CRITICAL') return '#b91c1c';
    if (l === 'HIGH') return '#c2410c';
    if (l === 'MEDIUM') return '#a16207';
    return '#15803d';
  };

  const getAgreementClass = (agr) => {
    const a = String(agr || '').toUpperCase();
    if (a.includes('RULE') && a.includes('STATISTICAL') && a.includes('ML')) return 'strong';
    if (a.includes('+')) return 'moderate';
    return 'single';
  };

  const statesList = Array.isArray(filters?.states) ? filters.states : [];
  const riskLevelsList = Array.isArray(filters?.risk_levels) ? filters.risk_levels : ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const prioritiesList = Array.isArray(filters?.priorities) ? filters.priorities : ['P1', 'P2', 'P3', 'P4'];
  const agreementsList = Array.isArray(filters?.detector_agreements) ? filters.detector_agreements : [
    'RULE + STATISTICAL + ML',
    'RULE + STATISTICAL',
    'RULE + ML',
    'STATISTICAL + ML',
    'RULE',
    'STATISTICAL',
    'ML'
  ];

  return (
    <div className="tactical-panel queue-container" id="section-queue">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <h3 className="panel-title">Investigation Queue</h3>
        </div>
        <div className="panel-actions">
          <span className="quick-metric-chip">
            <span className="chip-label">Candidates:</span>
            <span className="chip-value" style={{ color: '#0f172a' }}>
              {pagination.total != null ? pagination.total.toLocaleString() : 'Loading...'}
            </span>
          </span>
        </div>
      </div>

      {/* Filter and Search Controls Bar */}
      <div className="queue-controls-bar">
        <div className="search-filter-group" style={{ flexWrap: 'wrap', gap: '8px' }}>
          {/* Main Keyword Search */}
          <div className="tactical-search-input" style={{ minWidth: '240px', flex: '1 1 220px' }}>
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder="Search Work ID, MP, Constituency, Activity..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button 
                onClick={() => setSearch('')}
                style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}
                title="Clear search"
              >
                <X size={12} />
              </button>
            )}
          </div>

          {/* State Filter */}
          <select 
            className="tactical-select"
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            style={{ maxWidth: '180px' }}
          >
            <option value="ALL">All States / UTs</option>
            {statesList.map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          {/* Risk Level Filter */}
          <select 
            className="tactical-select"
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="ALL">All Risk Tiers</option>
            {riskLevelsList.map((lvl) => (
              <option key={lvl} value={lvl}>{lvl} Risk</option>
            ))}
          </select>

          {/* Priority Filter */}
          <select 
            className="tactical-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="ALL">All Priorities</option>
            {prioritiesList.map((p) => (
              <option key={p} value={p}>Priority {p}</option>
            ))}
          </select>

          {/* Detector Agreement Filter */}
          <select
            className="tactical-select"
            value={agreementFilter}
            onChange={(e) => setAgreementFilter(e.target.value)}
            style={{ maxWidth: '200px' }}
          >
            <option value="ALL">All Agreements</option>
            {agreementsList.map((agr) => (
              <option key={agr} value={agr}>{agr}</option>
            ))}
          </select>

          {/* Advanced Toggle (Constituency / MP) */}
          <button 
            className={`btn-tactical ${showAdvanced ? 'primary' : ''}`}
            onClick={() => setShowAdvanced(!showAdvanced)}
            title="Toggle Constituency & MP Filters"
          >
            <Filter size={12} />
            <span>More Filters</span>
          </button>

          {isFiltered && (
            <button className="btn-tactical" onClick={onClearFilters}>
              <X size={12} />
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* Secondary Filter Row (Constituency, MP) */}
        {showAdvanced && (
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #e5e8ee', flexWrap: 'wrap' }}>
            <div className="tactical-search-input" style={{ flex: '1 1 200px', maxWidth: '280px' }}>
              <MapPin size={13} color="#64748b" />
              <input
                type="text"
                placeholder="Filter by Constituency..."
                value={constituencyFilter === 'ALL' ? '' : constituencyFilter}
                onChange={(e) => setConstituencyFilter(e.target.value ? e.target.value : 'ALL')}
              />
              {constituencyFilter && constituencyFilter !== 'ALL' && (
                <button onClick={() => setConstituencyFilter('ALL')} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                  <X size={12} />
                </button>
              )}
            </div>

            <div className="tactical-search-input" style={{ flex: '1 1 200px', maxWidth: '280px' }}>
              <User size={13} color="#64748b" />
              <input
                type="text"
                placeholder="Filter by MP Name..."
                value={mpFilter === 'ALL' ? '' : mpFilter}
                onChange={(e) => setMpFilter(e.target.value ? e.target.value : 'ALL')}
              />
              {mpFilter && mpFilter !== 'ALL' && (
                <button onClick={() => setMpFilter('ALL')} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                  <X size={12} />
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Table View */}
      <div className="table-wrapper">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b', fontFamily: "'JetBrains Mono', monospace" }}>
            <div className="scanning-pip" style={{ margin: '0 auto 12px' }} />
            QUERYING INTELLIGENCE RECORDS...
          </div>
        ) : anomalies.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
            <FileText size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
            <div style={{ color: '#0f172a', fontSize: '13px', marginBottom: '6px', fontWeight: 600 }}>
              No matching work records found
            </div>
            <p style={{ fontSize: '12px', color: '#64748b' }}>
              Adjust search keywords or clear active state/risk/agreement filters to inspect the full dataset.
            </p>
          </div>
        ) : (
          <table className="tactical-table">
            <thead>
              <tr>
                <th>Work ID</th>
                <th>Member of Parliament / State</th>
                <th>Category & Scheme Activity</th>
                <th>Priority</th>
                <th>Risk Level</th>
                <th>Hybrid Score</th>
                <th>Consensus</th>
                <th>Detector Signals</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((item) => {
                const riskLvl = item.final_risk_level || 'LOW';
                const riskClass = getRiskClass(riskLvl);
                const agreementClass = getAgreementClass(item.detector_agreement);
                const priority = item.investigation_priority || 'P2';
                const rowClass = riskLvl === 'CRITICAL' ? 'row-high-priority' : riskLvl === 'HIGH' ? 'row-high-priority' : riskLvl === 'MEDIUM' ? 'row-med-priority' : 'row-low-priority';

                const priorityStyles = priority === 'P1'
                  ? { background: '#fef2f2', color: '#b91c1c', border: '1px solid #fca5a5' }
                  : priority === 'P2'
                  ? { background: '#fff7ed', color: '#c2410c', border: '1px solid #fdba74' }
                  : priority === 'P3'
                  ? { background: '#fefce8', color: '#a16207', border: '1px solid #fde047' }
                  : { background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1' };

                return (
                  <tr 
                    key={item.work_id} 
                    className={rowClass}
                    onClick={() => onOpenWork(item.work_id)}
                  >
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className="mono-id">#{item.work_id}</span>
                        {item.ai_available && (
                          <span title="AI Explanation Available">
                            <Sparkles size={11} />
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="mp-cell">
                        <span className="mp-name-text">{item.mp_name || 'Unspecified'}</span>
                        <span className="constituency-tag">
                          {item.state_name ? `${item.state_name} • ` : ''}{item.constituency || 'Constituency: —'}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span className="category-pill" title={item.work_category}>
                          {item.work_category || 'Normal/Others'}
                        </span>
                        {item.activity_name && (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '240px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.activity_name}>
                            {item.activity_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="mono-id" style={{ 
                        fontSize: '10px', 
                        padding: '2px 6px',
                        borderRadius: '2px',
                        ...priorityStyles
                      }}>
                        {priority}
                      </span>
                    </td>
                    <td>
                      <span className={`badge-risk ${riskClass}`}>
                        {riskLvl}
                      </span>
                    </td>
                    <td>
                      <span className="score-cell" style={{ color: getRiskColor(riskLvl) }}>
                        {item.hybrid_risk_score !== null && item.hybrid_risk_score !== undefined 
                          ? Number(item.hybrid_risk_score).toFixed(2) 
                          : '—'}
                      </span>
                    </td>
                    <td>
                      <span className="badge-agreement" title={item.detector_agreement}>
                        {item.detector_agreement_count ? `${item.detector_agreement_count}/3 Engines` : item.detector_agreement || 'None'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '3px', fontFamily: "'JetBrains Mono', monospace", fontSize: '9px' }}>
                        <span style={{ padding: '1px 4px', background: 'var(--bg-inset)', border: '1px solid var(--border-card)', borderRadius: '2px', color: 'var(--text-primary)', fontWeight: 700 }}>
                          R:{item.rule_score !== null && item.rule_score !== undefined ? item.rule_score : '—'}
                        </span>
                        <span style={{ padding: '1px 4px', background: 'var(--bg-inset)', border: '1px solid var(--border-card)', borderRadius: '2px', color: 'var(--text-primary)', fontWeight: 700 }}>
                          S:{item.statistical_score !== null && item.statistical_score !== undefined ? item.statistical_score : '—'}
                        </span>
                        <span style={{ padding: '1px 4px', background: 'var(--bg-inset)', border: '1px solid var(--border-card)', borderRadius: '2px', color: 'var(--text-primary)', fontWeight: 700 }}>
                          ML:{item.ml_score !== null && item.ml_score !== undefined ? item.ml_score : '—'}
                        </span>
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        className="btn-tactical primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenWork(item.work_id);
                        }}
                      >
                        <span>Dossier</span>
                        <ExternalLink size={11} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      <div className="pagination-bar">
        <div className="pagination-info">
          {pagination.total > 0 
            ? `Showing ${pagination.offset + 1} to ${Math.min(pagination.offset + pagination.limit, pagination.total)} of ${pagination.total.toLocaleString()} candidates`
            : 'No records found'}
        </div>

        <div className="pagination-controls">
          <button 
            className="page-btn" 
            disabled={pagination.offset <= 0 || loading}
            onClick={() => onPageChange(Math.max(0, pagination.offset - pagination.limit))}
            title="Previous Page"
          >
            <ChevronLeft size={14} />
          </button>

          <span className="page-btn active" style={{ width: 'auto', padding: '0 10px' }}>
            Page {currentPage} of {totalPages}
          </span>

          <button 
            className="page-btn" 
            disabled={pagination.offset + pagination.limit >= pagination.total || loading}
            onClick={() => onPageChange(pagination.offset + pagination.limit)}
            title="Next Page"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

