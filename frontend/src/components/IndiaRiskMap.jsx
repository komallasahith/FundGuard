import { useState, useMemo } from 'react';
import { Map as MapIcon, ChevronRight, Info } from 'lucide-react';
import { INDIA_MAP_PATHS } from '../data/indiaMapPaths.js';

function normalizeName(str) {
  return String(str || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]/g, '');
}

export default function IndiaRiskMap({ statesData = [], selectedState, onSelectState }) {
  const [mapMode, setMapMode] = useState('count'); // 'count' | 'rate'
  const [hoveredState, setHoveredState] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const safeStates = Array.isArray(statesData) ? statesData : [];

  // Map state records by normalized state name for instant O(1) lookup
  const stateDataMap = useMemo(() => {
    const map = new window.Map();
    const list = Array.isArray(statesData) ? statesData : [];
    for (const item of list) {
      if (!item) continue;
      const key = normalizeName(item.state_name || item.state);
      if (key) {
        map.set(key, {
          state: item.state_name || item.state,
          total_works: Number(item.analyzed_works ?? item.total_works ?? 0),
          candidates: Number(item.candidates ?? 0),
          rate: Number(item.candidate_rate_percent ?? item.rate ?? 0),
          critical: Number(item.critical ?? 0),
          high: Number(item.high ?? 0),
          medium: Number(item.medium ?? 0),
          low: Number(item.low ?? 0)
        });
      }
    }
    return map;
  }, [statesData]);

  const maxCandidateCount = useMemo(() => {
    if (!safeStates.length) return 1;
    return Math.max(...safeStates.map(s => Number(s?.candidates || 0)), 1);
  }, [safeStates]);

  const maxCandidateRate = useMemo(() => {
    if (!safeStates.length) return 1;
    return Math.max(...safeStates.map(s => Number(s?.candidate_rate_percent ?? s?.rate ?? 0)), 1);
  }, [safeStates]);

  const getStateInfo = (name) => {
    const key = normalizeName(name);
    return stateDataMap.get(key) || {
      state: name,
      total_works: 0,
      candidates: 0,
      rate: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };
  };

  const getColorForState = (info, isSelected) => {
    if (isSelected) return '#2563eb'; // vibrant royal blue
    if (!info || info.candidates === 0) return '#e2e8f0'; // clean light slate

    if (mapMode === 'count') {
      const ratio = info.candidates / maxCandidateCount;
      if (ratio > 0.5) return '#ef4444'; // vibrant crimson
      if (ratio > 0.25) return '#f97316'; // vibrant orange
      if (ratio > 0.08) return '#f59e0b'; // vibrant amber
      return '#93c5fd'; // soft blue
    } else {
      const ratio = info.rate / maxCandidateRate;
      if (ratio > 0.5) return '#ef4444';
      if (ratio > 0.25) return '#f97316';
      if (ratio > 0.12) return '#f59e0b';
      return '#93c5fd';
    }
  };

  // Compute active display state for inspector
  const activeDisplayState = useMemo(() => {
    if (hoveredState) return hoveredState;
    if (selectedState && selectedState !== 'ALL') {
      return getStateInfo(selectedState);
    }
    // Default to state with most candidates if available
    if (safeStates.length > 0 && safeStates[0]) {
      const topState = safeStates[0];
      return getStateInfo(topState.state_name || topState.state);
    }
    return getStateInfo('Uttar Pradesh');
  }, [hoveredState, selectedState, safeStates, stateDataMap]);

  // Sorted states list for ranking table
  const sortedStates = useMemo(() => {
    if (!safeStates.length) {
      return INDIA_MAP_PATHS.map(p => getStateInfo(p.name));
    }
    return safeStates
      .filter(Boolean)
      .map(s => ({
        state: s.state_name || s.state || 'Unknown',
        total_works: Number(s.analyzed_works ?? s.total_works ?? 0),
        candidates: Number(s.candidates ?? 0),
        rate: Number(s.candidate_rate_percent ?? s.rate ?? 0)
      }))
      .sort((a, b) => {
        if (mapMode === 'count') return b.candidates - a.candidates;
        return b.rate - a.rate;
      });
  }, [safeStates, mapMode, stateDataMap]);

  const handleMouseMove = (e, info) => {
    const rect = e.currentTarget.closest('.india-map-display-panel')?.getBoundingClientRect();
    if (rect) {
      setTooltipPos({
        x: e.clientX - rect.left + 15,
        y: e.clientY - rect.top - 10
      });
    }
    setHoveredState(info);
  };

  return (
    <section className="dashboard-section" id="section-map">
      <div className="section-header-block">
        <div className="section-title-wrap">
          <h2 className="section-main-heading">Investigation Candidates by State</h2>
        </div>
        
        {/* Toggle between Candidate Count & Candidate Rate */}
        <div className="map-controls-group">
          <div className="tab-pill-group">
            <button
              className={`tab-pill-btn ${mapMode === 'count' ? 'active' : ''}`}
              onClick={() => setMapMode('count')}
            >
              Candidate Count
            </button>
            <button
              className={`tab-pill-btn ${mapMode === 'rate' ? 'active' : ''}`}
              onClick={() => setMapMode('rate')}
            >
              Candidate Rate
            </button>
          </div>
        </div>
      </div>

      <div className="india-map-grid-container">
        {/* Real Geographic India SVG Map Panel */}
        <div className="india-map-display-panel" style={{ position: 'relative' }}>
          <div className="map-subhead-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapIcon size={15} />
              <span className="map-subhead-title">India State Map</span>
            </div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>
              Click any state to filter the investigation queue
            </span>
          </div>

          <div className="map-cartogram-viewport" style={{ padding: '12px 8px', display: 'flex', justifyContent: 'center' }}>
            <svg 
              viewBox="0 0 650 720" 
              className="real-india-svg"
              style={{ width: '100%', maxWidth: '580px', height: 'auto', maxHeight: '520px', display: 'block' }}
            >
              {/* Map Outline & State Boundaries */}
              <g className="india-state-polygons">
                {INDIA_MAP_PATHS.map((pathObj) => {
                  const info = getStateInfo(pathObj.name);
                  const isSelected = selectedState && normalizeName(selectedState) === normalizeName(pathObj.name);
                  const isHovered = hoveredState && normalizeName(hoveredState.state) === normalizeName(pathObj.name);
                  const fillColor = getColorForState(info, isSelected);

                  return (
                    <path
                      key={pathObj.id}
                      d={pathObj.path}
                      fill={fillColor}
                      stroke={isSelected ? '#38bdf8' : isHovered ? '#ffffff' : '#334155'}
                      strokeWidth={isSelected ? '2.5' : isHovered ? '1.8' : '1'}
                      strokeLinejoin="round"
                      strokeLinecap="round"
                      style={{ 
                        cursor: 'pointer',
                        transition: 'fill 0.15s ease, stroke 0.15s ease'
                      }}
                      onClick={() => onSelectState(info.state || pathObj.name)}
                      onMouseMove={(e) => handleMouseMove(e, info)}
                      onMouseLeave={() => setHoveredState(null)}
                    />
                  );
                })}
              </g>

              {/* State abbreviation / short code markers */}
              <g className="india-state-labels" pointerEvents="none">
                {INDIA_MAP_PATHS.map((pathObj) => {
                  if (!pathObj.labelX || !pathObj.labelY) return null;
                  const code = pathObj.id.replace('IN-', '');
                  return (
                    <text
                      key={`lbl-${pathObj.id}`}
                      x={pathObj.labelX}
                      y={pathObj.labelY}
                      textAnchor="middle"
                      fill="#94a3b8"
                      fontSize="10"
                      fontFamily="monospace"
                      fontWeight="600"
                    >
                      {code}
                    </text>
                  );
                })}
              </g>
            </svg>

            {/* Hover Tooltip */}
            {hoveredState && (
              <div 
                className="map-hover-tooltip"
                style={{
                  position: 'absolute',
                  left: `${tooltipPos.x}px`,
                  top: `${tooltipPos.y}px`,
                  backgroundColor: '#0f172a',
                  border: '1px solid #334155',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  pointerEvents: 'none',
                  zIndex: 50,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  minWidth: '180px'
                }}
              >
                <div style={{ fontWeight: '700', fontSize: '13px', color: '#f8fafc', marginBottom: '4px' }}>
                  {hoveredState.state}
                </div>
                <div style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.4' }}>
                  <div>Works Analyzed: <strong style={{ color: '#fff' }}>{hoveredState.total_works.toLocaleString()}</strong></div>
                  <div>Investigation Candidates: <strong style={{ color: '#f87171' }}>{hoveredState.candidates.toLocaleString()}</strong></div>
                  <div>Candidate Rate: <strong style={{ color: '#38bdf8' }}>{hoveredState.rate.toFixed(2)}%</strong></div>
                </div>
              </div>
            )}

            {/* Map Legend */}
            <div className="map-legend-overlay">
              <span className="legend-label-title">
                {mapMode === 'count' ? 'Candidate Intensity' : 'Candidate Rate Intensity'}
              </span>
              <div className="legend-gradient-bar">
                <div className="legend-color-stop" style={{ background: '#1e293b' }} title="0 / Minimal" />
                <div className="legend-color-stop" style={{ background: '#334155' }} title="Low" />
                <div className="legend-color-stop" style={{ background: '#854d0e' }} title="Medium" />
                <div className="legend-color-stop" style={{ background: '#9a3412' }} title="High" />
                <div className="legend-color-stop" style={{ background: '#991b1b' }} title="Critical Concentration" />
              </div>
              <div className="legend-values-row">
                <span>0</span>
                <span>{mapMode === 'count' ? `${maxCandidateCount.toLocaleString()} candidates` : `${maxCandidateRate.toFixed(2)}% rate`}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Selected State Panel & State List */}
        <div className="india-map-inspector-panel">
          {/* Selected State Card */}
          <div className="state-inspector-card">
            <div className="inspector-card-header">
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span className="inspector-kicker">Selected State</span>
                <h3 className="inspector-state-name">{activeDisplayState.state}</h3>
              </div>
              <button 
                className={`btn-select-state ${selectedState === activeDisplayState.state ? 'active' : ''}`}
                onClick={() => onSelectState(activeDisplayState.state)}
                title="Filter Investigation Queue to this state"
              >
                <span>{selectedState === activeDisplayState.state ? 'Clear Filter' : 'Filter Queue'}</span>
                <ChevronRight size={13} />
              </button>
            </div>

            <div className="inspector-metrics-grid">
              <div className="inspector-kv-box">
                <span className="inspector-kv-label">Works Analyzed</span>
                <span className="inspector-kv-val">{activeDisplayState.total_works.toLocaleString()}</span>
              </div>
              <div className="inspector-kv-box highlight-amber">
                <span className="inspector-kv-label">Investigation Candidates</span>
                <span className="inspector-kv-val">{activeDisplayState.candidates.toLocaleString()}</span>
              </div>
              <div className="inspector-kv-box highlight-cyan">
                <span className="inspector-kv-label">Candidate Rate</span>
                <span className="inspector-kv-val">{activeDisplayState.rate.toFixed(2)}%</span>
              </div>
            </div>

            <div className="inspector-notice-bar">
              <Info size={13} color="#94a3b8" style={{ flexShrink: 0 }} />
              <span>
                State values reflect candidate frequency relative to total reported works in {activeDisplayState.state}.
              </span>
            </div>
          </div>

          {/* All-India State Table */}
          <div className="state-ranking-table-card">
            <div className="ranking-card-header">
              <span className="ranking-title">State-Wise Breakdown ({sortedStates.length} States / UTs)</span>
            </div>

            <div className="state-ranking-scroll-list">
              {sortedStates.map((s, idx) => {
                const isSelected = selectedState && normalizeName(selectedState) === normalizeName(s.state);
                return (
                  <div 
                    key={s.state}
                    className={`state-rank-row ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectState(s.state)}
                  >
                    <span className="rank-num">#{idx + 1}</span>
                    <span className="rank-state-name">{s.state}</span>
                    <span className="rank-works-count">{s.total_works.toLocaleString()} works</span>
                    <span className="rank-candidates-pill">{s.candidates.toLocaleString()} flags</span>
                    <span className="rank-rate-text">{s.rate.toFixed(2)}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
