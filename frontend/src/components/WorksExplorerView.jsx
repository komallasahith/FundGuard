import { useState } from 'react';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Sparkles, 
  ExternalLink, 
  Filter, 
  X, 
  Database,
  FileSpreadsheet,
  AlertTriangle,
  Layers,
  ArrowUpDown
} from 'lucide-react';

export default function WorksExplorerView({
  anomalies = [],
  loading,
  filters,
  search,
  setSearch,
  scope,
  setScope,
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
  const [showFilters, setShowFilters] = useState(false);

  const totalRecords = pagination?.total ?? 7521;
  const limit = pagination?.limit ?? 50;
  const offset = pagination?.offset ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalRecords / limit));
  const currentPage = Math.floor(offset / limit) + 1;

  const hasActiveFilters = Boolean(
    (search && search.trim()) ||
    (stateFilter && stateFilter !== 'ALL') ||
    (constituencyFilter && constituencyFilter !== 'ALL') ||
    (mpFilter && mpFilter !== 'ALL') ||
    (riskFilter && riskFilter !== 'ALL') ||
    (priorityFilter && priorityFilter !== 'ALL') ||
    (agreementFilter && agreementFilter !== 'ALL')
  );

  const getRiskBadgeClass = (riskLevel) => {
    const lvl = String(riskLevel || 'LOW').toUpperCase();
    if (lvl === 'CRITICAL') return 'badge-crit';
    if (lvl === 'HIGH') return 'badge-high';
    if (lvl === 'MEDIUM') return 'badge-med';
    return 'badge-low';
  };

  const getPriorityBadgeClass = (p) => {
    const pStr = String(p || 'P2').toUpperCase();
    if (pStr === 'P1') return 'p-badge-p1';
    if (pStr === 'P2') return 'p-badge-p2';
    if (pStr === 'P3') return 'p-badge-p3';
    return 'p-badge-p4';
  };

  const getAgreementClass = (agr, count) => {
    if (count === 3 || String(agr).includes('RULE') && String(agr).includes('STATISTICAL') && String(agr).includes('ML')) {
      return 'agr-strong';
    }
    if (count === 2 || String(agr).includes('TWO')) {
      return 'agr-moderate';
    }
    return 'agr-single';
  };

  return (
    <div className="view-container">
      {/* Top Header Row with Scope Switcher */}
      <div className="explorer-header-card">
        <div className="explorer-header-left">
          <h1 className="explorer-title">National Works & Anomaly Database</h1>
          <p className="explorer-subtitle">
            Comprehensive multi-detector query engine across all 104,517 canonical MPLADS works and 7,521 prioritized anomaly candidates.
          </p>
        </div>

        {/* Scope Switcher Buttons */}
        <div className="scope-toggle-group">
          <button 
            className={`scope-btn ${scope === 'candidates' ? 'scope-active' : ''}`}
            onClick={() => {
              setScope('candidates');
              onPageChange(0);
            }}
          >
            <AlertTriangle size={13} color={scope === 'candidates' ? '#b91c1c' : '#64748b'} />
            <span>Investigation Candidates (7,521)</span>
          </button>
          <button 
            className={`scope-btn ${scope === 'all' ? 'scope-active' : ''}`}
            onClick={() => {
              setScope('all');
              onPageChange(0);
            }}
          >
            <Database size={13} color={scope === 'all' ? '#2563eb' : '#64748b'} />
            <span>All National Works (104,517)</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="explorer-filter-card">
        <div className="filter-row-top">
          {/* Main Keyword Search */}
          <div className="explorer-search-input">
            <Search size={15} color="#64748b" />
            <input 
              type="text"
              placeholder="Search by Work ID, MP Name, Constituency, State, Activity Description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button className="btn-clear-search" onClick={() => setSearch('')}>
                <X size={13} />
              </button>
            )}
          </div>

          {/* Filter Dropdowns */}
          <div className="filter-dropdowns-group">
            {/* State Filter */}
            <div className="select-wrap">
              <span className="select-label">State:</span>
              <select 
                value={stateFilter} 
                onChange={(e) => {
                  setStateFilter(e.target.value);
                  setConstituencyFilter('ALL');
                  setMpFilter('ALL');
                }}
              >
                <option value="ALL">All 36 States/UTs</option>
                {filters?.states?.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            {/* Risk Tier Filter */}
            <div className="select-wrap">
              <span className="select-label">Risk:</span>
              <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
                <option value="ALL">All Risk Tiers</option>
                <option value="CRITICAL">Critical Risk (P1)</option>
                <option value="HIGH">High Risk (P2)</option>
                <option value="MEDIUM">Medium Risk (P3)</option>
                <option value="LOW">Low Risk (P4)</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div className="select-wrap">
              <span className="select-label">Priority:</span>
              <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
                <option value="ALL">All Priorities</option>
                <option value="P1">P1 (Immediate Review)</option>
                <option value="P2">P2 (High Verification)</option>
                <option value="P3">P3 (Routine Audit)</option>
                <option value="P4">P4 (Screening Tier)</option>
              </select>
            </div>

            {/* Detector Agreement Filter */}
            <div className="select-wrap">
              <span className="select-label">Consensus:</span>
              <select value={agreementFilter} onChange={(e) => setAgreementFilter(e.target.value)}>
                <option value="ALL">All Consensus Tiers</option>
                <option value="RULE + STATISTICAL + ML">All 3 Engines (Strong)</option>
                <option value="TWO METHODS AGREE">2 Engines (Moderate)</option>
                <option value="ONE METHOD">1 Engine (Single)</option>
              </select>
            </div>

            {hasActiveFilters && (
              <button className="btn-reset-filters" onClick={onClearFilters}>
                <X size={13} />
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Record Count Telemetry */}
        <div className="filter-summary-row">
          <span className="records-count-text">
            Showing <strong>{Math.min(offset + 1, totalRecords).toLocaleString()} – {Math.min(offset + limit, totalRecords).toLocaleString()}</strong> of <strong>{totalRecords.toLocaleString()}</strong> records
          </span>
          {hasActiveFilters && (
            <span className="active-filters-badge">
              <Filter size={11} />
              <span>Filters Applied</span>
            </span>
          )}
        </div>
      </div>

      {/* Main Data Table */}
      <div className="explorer-table-card">
        <div className="table-responsive-wrapper">
          <table className="govtech-data-table">
            <thead>
              <tr>
                <th style={{ width: '110px' }}>Work ID</th>
                <th style={{ width: '180px' }}>State / Constituency</th>
                <th style={{ width: '170px' }}>Member of Parliament</th>
                <th>Work Category & Description</th>
                <th style={{ width: '80px' }}>Priority</th>
                <th style={{ width: '100px' }}>Risk Level</th>
                <th style={{ width: '90px' }}>Risk Score</th>
                <th style={{ width: '130px' }}>Detector Agreement</th>
                <th style={{ width: '130px' }}>Engine Signals</th>
                <th style={{ width: '90px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="10" className="table-loading-cell">
                    <div className="loading-row">
                      <span className="loading-spinner" />
                      <span>Loading records from National Index...</span>
                    </div>
                  </td>
                </tr>
              ) : anomalies.length === 0 ? (
                <tr>
                  <td colSpan="10" className="table-empty-cell">
                    <div className="empty-state-box">
                      <AlertTriangle size={24} color="#94a3b8" />
                      <span className="empty-title">No matching works found</span>
                      <span className="empty-desc">Try clearing or adjusting search queries and filter parameters.</span>
                      {hasActiveFilters && (
                        <button className="btn-hero-primary" onClick={onClearFilters} style={{ marginTop: '10px' }}>
                          Clear All Filters
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                anomalies.map((work) => {
                  const workId = work.work_id || work.WORK_ID;
                  const riskLvl = String(work.final_risk_level || work.risk_level || 'LOW').toUpperCase();
                  const priority = work.investigation_priority || 'P2';
                  const score = work.hybrid_risk_score != null ? Number(work.hybrid_risk_score).toFixed(1) : '—';
                  const agr = work.detector_agreement || 'Single';
                  const count = work.detector_agreement_count || 1;

                  return (
                    <tr 
                      key={workId} 
                      className="table-data-row"
                      onClick={() => onOpenWork(workId)}
                    >
                      <td>
                        <div className="work-id-cell">
                          <span className="work-id-tag">#{workId}</span>
                          {work.ai_available && (
                            <span className="ai-sparkle-icon" title="AI Investigation Explanation Available">
                              <Sparkles size={11} color="#16a34a" />
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="location-cell">
                          <span className="state-text">{work.state_name || 'India'}</span>
                          <span className="constituency-text">{work.constituency || 'Constituency: —'}</span>
                        </div>
                      </td>
                      <td>
                        <span className="mp-text">{work.mp_name || 'Unspecified MP'}</span>
                      </td>
                      <td>
                        <div className="desc-cell">
                          <span className="cat-pill">{work.work_category || 'General'}</span>
                          <span className="desc-text" title={work.work_description || work.activity_name}>
                            {work.work_description || work.activity_name || 'No description available'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={`priority-badge ${getPriorityBadgeClass(priority)}`}>
                          {priority}
                        </span>
                      </td>
                      <td>
                        <span className={`risk-badge ${getRiskBadgeClass(riskLvl)}`}>
                          {riskLvl}
                        </span>
                      </td>
                      <td>
                        <span className="score-mono">{score}</span>
                      </td>
                      <td>
                        <span className={`agreement-badge ${getAgreementClass(agr, count)}`}>
                          {count}/3 Engines
                        </span>
                      </td>
                      <td>
                        <div className="signals-row">
                          <span className="sig-badge" title="Rule Detector Score">R:{work.rule_score != null ? work.rule_score : '—'}</span>
                          <span className="sig-badge" title="Statistical Peer Score">S:{work.statistical_score != null ? work.statistical_score : '—'}</span>
                          <span className="sig-badge" title="Isolation Forest ML Score">ML:{work.ml_score != null ? work.ml_score : '—'}</span>
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button 
                          className="btn-inspect-action"
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenWork(workId);
                          }}
                        >
                          <span>Inspect</span>
                          <ExternalLink size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="table-pagination-bar">
          <div className="pagination-info">
            Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong> ({totalRecords.toLocaleString()} works)
          </div>

          <div className="pagination-buttons">
            <button 
              className="page-btn"
              disabled={currentPage <= 1 || loading}
              onClick={() => onPageChange(0)}
              title="First Page"
            >
              First
            </button>
            <button 
              className="page-btn"
              disabled={currentPage <= 1 || loading}
              onClick={() => onPageChange(Math.max(0, offset - limit))}
            >
              <ChevronLeft size={14} />
              <span>Previous</span>
            </button>
            <button 
              className="page-btn"
              disabled={currentPage >= totalPages || loading}
              onClick={() => onPageChange(offset + limit)}
            >
              <span>Next</span>
              <ChevronRight size={14} />
            </button>
            <button 
              className="page-btn"
              disabled={currentPage >= totalPages || loading}
              onClick={() => onPageChange((totalPages - 1) * limit)}
              title="Last Page"
            >
              Last
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
