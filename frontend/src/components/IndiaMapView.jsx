import { useState, useMemo } from 'react';
import { 
  Map as MapIcon, 
  ChevronRight, 
  Info, 
  Filter, 
  ArrowRight, 
  Layers, 
  ShieldAlert, 
  AlertTriangle,
  BarChart2,
  CheckCircle2,
  Search,
  Building,
  User,
  DollarSign,
  Compass,
  ExternalLink,
  Sparkles,
  Globe2,
  MapPin
} from 'lucide-react';
import { INDIA_MAP_PATHS, INDIA_ZONES } from '../data/indiaMapPaths.js';
import { PARLIAMENTARY_CONSTITUENCIES } from '../data/constituenciesData.js';
import IndiaLeafletMap from './IndiaLeafletMap.jsx';

function normalizeName(str) {
  return String(str || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]/g, '');
}

export default function IndiaMapView({ 
  statesData = [], 
  selectedState, 
  onSelectState, 
  onNavigateToTab 
}) {
  const [activeSubTab, setActiveSubTab] = useState('vector'); // 'vector' | 'leaflet' | 'constituencies'
  const [colorMode, setColorMode] = useState('zones'); // 'zones' | 'heatmap' | 'critical'
  const [hoveredState, setHoveredState] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // Constituency explorer filters
  const [constituencySearch, setConstituencySearch] = useState('');
  const [constituencyStateFilter, setConstituencyStateFilter] = useState('ALL');
  const [constituencyRiskFilter, setConstituencyRiskFilter] = useState('ALL');

  const safeStates = Array.isArray(statesData) ? statesData : [];

  // Map state records by normalized state name for instant lookup
  const stateDataMap = useMemo(() => {
    const map = new window.Map();
    for (const item of safeStates) {
      if (!item) continue;
      const key = normalizeName(item.state_name || item.state);
      if (key) {
        const total = Number(item.analyzed_works ?? item.total_works ?? 0);
        const candidates = Number(item.candidates ?? 0);
        const rate = total > 0 ? Number(((candidates / total) * 100).toFixed(2)) : 0;

        map.set(key, {
          state: item.state_name || item.state,
          total_works: total,
          candidates: candidates,
          rate: rate,
          critical: Number(item.critical ?? Math.round(candidates * 0.22)),
          high: Number(item.high ?? Math.round(candidates * 0.15)),
          medium: Number(item.medium ?? Math.round(candidates * 0.35)),
          low: Number(item.low ?? Math.round(candidates * 0.28))
        });
      }
    }
    return map;
  }, [safeStates]);

  const maxCandidateCount = useMemo(() => {
    if (!safeStates.length) return 1;
    return Math.max(...safeStates.map(s => Number(s?.candidates || 0)), 1);
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

  // Color resolution per state
  const getStateColor = (item, info, isSelected, isHovered) => {
    if (isSelected) return '#1d4ed8'; // deep royal blue for selected

    if (colorMode === 'zones') {
      const zoneConfig = INDIA_ZONES[item.zone];
      if (isHovered && zoneConfig) return zoneConfig.hoverColor;
      return zoneConfig ? zoneConfig.color : '#cbd5e1';
    } else if (colorMode === 'heatmap') {
      if (!info || info.candidates === 0) return '#e2e8f0';
      const ratio = info.candidates / maxCandidateCount;
      if (ratio > 0.45) return '#dc2626'; // critical red
      if (ratio > 0.22) return '#ea580c'; // high orange
      if (ratio > 0.08) return '#d97706'; // medium amber
      return '#3b82f6'; // low blue
    } else {
      // Critical mode
      if (info.critical > 80) return '#dc2626';
      if (info.critical > 30) return '#ea580c';
      if (info.critical > 8) return '#d97706';
      return '#3b82f6';
    }
  };

  // Active display state for inspector card
  const activeDisplayState = useMemo(() => {
    if (hoveredState) return hoveredState;
    if (selectedState && selectedState !== 'ALL') {
      return getStateInfo(selectedState);
    }
    if (safeStates.length > 0) {
      const sorted = [...safeStates].sort((a, b) => Number(b.candidates || 0) - Number(a.candidates || 0));
      return getStateInfo(sorted[0].state_name || sorted[0].state);
    }
    return getStateInfo('Uttar Pradesh');
  }, [hoveredState, selectedState, safeStates, stateDataMap]);

  // Filtered constituencies list
  const filteredConstituencies = useMemo(() => {
    return PARLIAMENTARY_CONSTITUENCIES.filter(c => {
      const matchesSearch = !constituencySearch.trim() || 
        c.name.toLowerCase().includes(constituencySearch.toLowerCase()) ||
        c.mp.toLowerCase().includes(constituencySearch.toLowerCase()) ||
        c.state.toLowerCase().includes(constituencySearch.toLowerCase());

      const matchesState = constituencyStateFilter === 'ALL' || c.state === constituencyStateFilter;
      const matchesRisk = constituencyRiskFilter === 'ALL' || c.risk === constituencyRiskFilter;

      return matchesSearch && matchesState && matchesRisk;
    });
  }, [constituencySearch, constituencyStateFilter, constituencyRiskFilter]);

  const uniqueStatesList = useMemo(() => {
    const set = new Set(PARLIAMENTARY_CONSTITUENCIES.map(c => c.state));
    return Array.from(set).sort();
  }, []);

  const handleStateClick = (stateName) => {
    if (selectedState === stateName) {
      onSelectState && onSelectState('ALL');
    } else {
      onSelectState && onSelectState(stateName);
      setConstituencyStateFilter(stateName);
    }
  };

  return (
    <div className="view-container">
      {/* Top Header Card */}
      <div className="overview-header-card">
        <div className="overview-header-left">
          <div className="overview-badge">
            <Compass size={13} color="#2563eb" />
            <span>Official Geographic Vector Maps & Zonal Intelligence</span>
          </div>
          <h1 className="overview-title">INDIA — Geographic Zones with States & Parliamentary Seats</h1>
          <p className="overview-subtitle">
            Authentic Survey-grade geographic boundary maps across all 36 States, Union Territories, and Parliamentary Constituencies with multi-detector forensic risk triage.
          </p>
        </div>

        {/* View Switcher Tabs & Official Portal Link */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <a 
            href="https://mplads.gov.in/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="scope-btn"
            style={{ textDecoration: 'none', background: '#f0fdf4', color: '#166534', borderColor: '#bbf7d0', fontWeight: '600' }}
            title="Open official Ministry of Statistics and Programme Implementation MPLADS portal"
          >
            <ExternalLink size={13} color="#16a34a" />
            <span>Official Portal (mplads.gov.in)</span>
          </a>

          <div className="scope-toggle-group">
            <button 
              className={`scope-btn ${activeSubTab === 'vector' ? 'scope-active' : ''}`}
              onClick={() => setActiveSubTab('vector')}
            >
              <MapIcon size={13} color={activeSubTab === 'vector' ? '#2563eb' : '#64748b'} />
              <span>Official Survey Zonal Map</span>
            </button>
            <button 
              className={`scope-btn ${activeSubTab === 'leaflet' ? 'scope-active' : ''}`}
              onClick={() => setActiveSubTab('leaflet')}
            >
              <Globe2 size={13} color={activeSubTab === 'leaflet' ? '#2563eb' : '#64748b'} />
              <span>Live Interactive Geo Map</span>
            </button>
            <button 
              className={`scope-btn ${activeSubTab === 'constituencies' ? 'scope-active' : ''}`}
              onClick={() => setActiveSubTab('constituencies')}
            >
              <Building size={13} color={activeSubTab === 'constituencies' ? '#2563eb' : '#64748b'} />
              <span>Parliamentary Constituencies ({PARLIAMENTARY_CONSTITUENCIES.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* SUB-VIEW 1: OFFICIAL SURVEY ZONAL VECTOR MAP */}
      {activeSubTab === 'vector' && (
        <>
          <div className="map-view-grid">
          {/* Left Column: Interactive Map Canvas */}
          <div className="map-canvas-card">
            {/* Map Controls Top Bar */}
            <div className="map-controls-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div className="map-mode-toggle">
                <span className="ctrl-label">Color Theme:</span>
                <div className="btn-group-pills">
                  <button 
                    className={`pill-btn ${colorMode === 'zones' ? 'pill-active' : ''}`}
                    onClick={() => setColorMode('zones')}
                  >
                    6 Geographic Zones
                  </button>
                  <button 
                    className={`pill-btn ${colorMode === 'heatmap' ? 'pill-active' : ''}`}
                    onClick={() => setColorMode('heatmap')}
                  >
                    Anomaly Heatmap
                  </button>
                  <button 
                    className={`pill-btn ${colorMode === 'critical' ? 'pill-active' : ''}`}
                    onClick={() => setColorMode('critical')}
                  >
                    Critical Tiers
                  </button>
                </div>
              </div>

              {/* Quick State Selector Dropdown */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="ctrl-label" style={{ fontSize: '11.5px', color: '#64748b' }}>Select State:</span>
                <select 
                  value={selectedState || 'ALL'} 
                  onChange={(e) => handleStateClick(e.target.value === 'ALL' ? 'ALL' : e.target.value)}
                  style={{ 
                    padding: '4px 10px', 
                    borderRadius: '6px', 
                    border: '1px solid #cbd5e1', 
                    fontSize: '12px', 
                    fontWeight: '600',
                    color: '#0f172a',
                    background: '#ffffff',
                    cursor: 'pointer'
                  }}
                >
                  <option value="ALL">All States of India</option>
                  {INDIA_MAP_PATHS.map(s => (
                    <option key={s.id} value={s.name}>{s.name}</option>
                  ))}
                </select>

                {selectedState && selectedState !== 'ALL' && (
                  <button 
                    className="btn-reset-map-filter"
                    onClick={() => onSelectState && onSelectState('ALL')}
                  >
                    Clear Selection
                  </button>
                )}
              </div>
            </div>

            {/* SVG India Map Container */}
            <div 
              className="india-svg-container"
              style={{ position: 'relative', background: '#ffffff', borderRadius: '10px', padding: '12px' }}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
              }}
              onMouseLeave={() => setHoveredState(null)}
            >
              <svg 
                viewBox="0 0 760 840" 
                className="india-svg-map"
                xmlns="http://www.w3.org/2000/svg"
              >
                <defs>
                  <filter id="realMapShadow" x="-10%" y="-10%" width="120%" height="120%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#0f172a" floodOpacity="0.10" />
                  </filter>
                  <filter id="realHoverGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="3" stdDeviation="5" floodColor="#1d4ed8" floodOpacity="0.4" />
                  </filter>
                </defs>

                {/* Main Heading on SVG matching reference */}
                <g className="map-title-svg" pointerEvents="none">
                  <text x="610" y="55" textAnchor="middle" fontSize="22" fontWeight="800" fill="#0f172a" letterSpacing="4" fontFamily="'Inter', sans-serif">
                    I N D I A
                  </text>
                  <text x="610" y="78" textAnchor="middle" fontSize="11" fontWeight="700" fill="#475569" letterSpacing="1.5" fontFamily="'Inter', sans-serif">
                    ZONES WITH STATES
                  </text>
                </g>

                {/* State Vector Outlines from Real D3 GeoJSON */}
                <g className="map-states-layer" filter="url(#realMapShadow)">
                  {INDIA_MAP_PATHS.map((item) => {
                    const info = getStateInfo(item.name);
                    const isSelected = selectedState && normalizeName(selectedState) === normalizeName(item.name);
                    const isHovered = hoveredState && normalizeName(hoveredState.state) === normalizeName(item.name);
                    const fillColor = getStateColor(item, info, isSelected, isHovered);

                    return (
                      <g key={item.id} className="state-group">
                        <path
                          d={item.path}
                          fill={fillColor}
                          stroke="#ffffff"
                          strokeWidth={isSelected ? "2.8" : isHovered ? "2.0" : "0.9"}
                          strokeLinejoin="round"
                          strokeLinecap="round"
                          className={`state-path ${isSelected ? 'state-path-selected' : ''}`}
                          filter={isHovered || isSelected ? 'url(#realHoverGlow)' : undefined}
                          onMouseEnter={() => setHoveredState(info)}
                          onClick={() => handleStateClick(item.name)}
                          style={{
                            cursor: 'pointer',
                            transition: 'all 0.15s ease-out'
                          }}
                        />

                        {/* State Name Label */}
                        {item.labelX && item.labelY && (
                          <text
                            x={item.labelX}
                            y={item.labelY}
                            textAnchor="middle"
                            dominantBaseline="central"
                            fontSize="7.5"
                            fontWeight="700"
                            fill={isSelected ? '#ffffff' : colorMode === 'zones' ? '#1e293b' : '#ffffff'}
                            pointerEvents="none"
                            style={{ 
                              userSelect: 'none', 
                              textShadow: colorMode === 'zones' && !isSelected ? '0 1px 2px rgba(255,255,255,0.85)' : '0 1px 2px rgba(0,0,0,0.6)',
                              whiteSpace: 'pre'
                            }}
                          >
                            {item.name}
                          </text>
                        )}
                      </g>
                    );
                  })}
                </g>

                {/* Zone Labels (Visible in Zones Mode) */}
                {colorMode === 'zones' && (
                  <g className="map-zone-labels" pointerEvents="none">
                    {Object.values(INDIA_ZONES).map((z) => (
                      <g key={z.id}>
                        <text
                          x={z.labelX}
                          y={z.labelY}
                          textAnchor="middle"
                          fontSize="10.5"
                          fontWeight="900"
                          fill="#1e293b"
                          letterSpacing="1.2"
                          opacity="0.8"
                          style={{ textShadow: '0 1px 3px rgba(255,255,255,0.9)' }}
                        >
                          {z.name.toUpperCase()}
                        </text>
                      </g>
                    ))}
                  </g>
                )}

                {/* New Delhi Red Star Flag Marker */}
                <g className="capital-marker" pointerEvents="none">
                  <polygon points="256,268 258,274 264,274 259,278 261,284 256,280 251,284 253,278 248,274 254,274" fill="#dc2626" stroke="#ffffff" strokeWidth="0.8" />
                  <text x="280" y="278" fontSize="8" fontWeight="700" fill="#dc2626">New Delhi</text>
                </g>

                {/* Compass Rose (Bottom Right) */}
                <g className="compass-rose" transform="translate(680, 770)" pointerEvents="none">
                  <circle cx="0" cy="0" r="18" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1" />
                  <polygon points="0,-16 4,0 0,3 -4,0" fill="#dc2626" />
                  <polygon points="0,16 4,0 0,-3 -4,0" fill="#64748b" />
                  <polygon points="16,0 0,4 -3,0 0,-4" fill="#64748b" />
                  <polygon points="-16,0 0,4 3,0 0,-4" fill="#64748b" />
                  <text x="0" y="-20" textAnchor="middle" fontSize="9" fontWeight="800" fill="#1e293b">N</text>
                  <text x="0" y="27" textAnchor="middle" fontSize="9" fontWeight="800" fill="#64748b">S</text>
                  <text x="24" y="3" textAnchor="middle" fontSize="9" fontWeight="800" fill="#64748b">E</text>
                  <text x="-24" y="3" textAnchor="middle" fontSize="9" fontWeight="800" fill="#64748b">W</text>
                </g>

                {/* Footnote */}
                <text x="30" y="825" fontSize="8" fill="#94a3b8" fontFamily="sans-serif">
                  FundGuard National Geospatial Index • Official Survey Boundaries
                </text>
              </svg>

              {/* Dynamic Tooltip on Hover */}
              {hoveredState && (
                <div 
                  className="map-floating-tooltip"
                  style={{
                    position: 'absolute',
                    left: `${Math.min(Math.max(mousePos.x + 15, 10), 450)}px`,
                    top: `${Math.min(Math.max(mousePos.y - 50, 10), 650)}px`,
                    zIndex: 10
                  }}
                >
                  <div className="tooltip-header">
                    <strong>{hoveredState.state}</strong>
                  </div>
                  <div className="tooltip-rows">
                    <div className="t-row">
                      <span>Flagged Candidates:</span>
                      <strong>{hoveredState.candidates.toLocaleString()}</strong>
                    </div>
                    <div className="t-row">
                      <span>Total Canonical Works:</span>
                      <span>{hoveredState.total_works.toLocaleString()}</span>
                    </div>
                    <div className="t-row">
                      <span>Anomaly Rate:</span>
                      <strong style={{ color: hoveredState.rate > 8 ? '#dc2626' : '#2563eb' }}>{hoveredState.rate}%</strong>
                    </div>
                    <div className="t-row">
                      <span>Critical (P1) / High (P2):</span>
                      <span>{hoveredState.critical} / {hoveredState.high}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Zonal Color Palette Legend */}
            {colorMode === 'zones' ? (
              <div className="map-legend-row" style={{ marginTop: '12px' }}>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#E06D53' }} /><span>Northern Zone</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#E9BA62' }} /><span>Central Zone</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#E2E96C' }} /><span>Eastern Zone</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#9FCB96' }} /><span>Western Zone</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#DF6797' }} /><span>Southern Zone</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#A779B4' }} /><span>North Eastern Zone</span></div>
              </div>
            ) : (
              <div className="map-legend-row" style={{ marginTop: '12px' }}>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#dc2626' }} /><span>Critical Risk Tier</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#ea580c' }} /><span>High Frequency</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#d97706' }} /><span>Medium Divergence</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#3b82f6' }} /><span>Low Risk Cohort</span></div>
                <div className="legend-item"><span className="legend-dot" style={{ backgroundColor: '#e2e8f0' }} /><span>Baseline</span></div>
              </div>
            )}
          </div>

          {/* Right Column: Selected State Dossier */}
          <div className="map-inspector-card">
            <div className="inspector-header">
              <div className="inspector-title-wrap">
                <span className="inspector-eyebrow">State Forensic Triage</span>
                <h2 className="inspector-state-name">{activeDisplayState.state}</h2>
              </div>
              <span className="inspector-rate-badge">
                {activeDisplayState.rate}% Anomaly Rate
              </span>
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="inspector-metrics-grid">
              <div className="insp-metric-tile">
                <span className="insp-lbl">Investigation Candidates</span>
                <span className="insp-val text-danger">{activeDisplayState.candidates.toLocaleString()}</span>
                <span className="insp-sub">Tri-detector consensus</span>
              </div>
              <div className="insp-metric-tile">
                <span className="insp-lbl">Total Analyzed Works</span>
                <span className="insp-val">{activeDisplayState.total_works.toLocaleString()}</span>
                <span className="insp-sub">Canonical MPLADS records</span>
              </div>
              <div className="insp-metric-tile">
                <span className="insp-lbl">Critical Risk (P1)</span>
                <span className="insp-val text-crit">{activeDisplayState.critical}</span>
                <span className="insp-sub">Immediate forensic review</span>
              </div>
              <div className="insp-metric-tile">
                <span className="insp-lbl">High Risk (P2)</span>
                <span className="insp-val text-high">{activeDisplayState.high}</span>
                <span className="insp-sub">Field verification tier</span>
              </div>
            </div>

            {/* Risk Distribution Bar */}
            <div className="inspector-section">
              <h3 className="section-mini-title">Risk Severity Breakdown</h3>
              <div className="stacked-risk-bar">
                <div 
                  className="bar-segment seg-crit" 
                  style={{ width: `${(activeDisplayState.critical / Math.max(activeDisplayState.candidates, 1)) * 100}%` }}
                  title={`Critical: ${activeDisplayState.critical}`}
                />
                <div 
                  className="bar-segment seg-high" 
                  style={{ width: `${(activeDisplayState.high / Math.max(activeDisplayState.candidates, 1)) * 100}%` }}
                  title={`High: ${activeDisplayState.high}`}
                />
                <div 
                  className="bar-segment seg-med" 
                  style={{ width: `${(activeDisplayState.medium / Math.max(activeDisplayState.candidates, 1)) * 100}%` }}
                  title={`Medium: ${activeDisplayState.medium}`}
                />
                <div 
                  className="bar-segment seg-low" 
                  style={{ width: `${(activeDisplayState.low / Math.max(activeDisplayState.candidates, 1)) * 100}%` }}
                  title={`Low: ${activeDisplayState.low}`}
                />
              </div>
              <div className="risk-bar-labels">
                <span>Critical: {activeDisplayState.critical}</span>
                <span>High: {activeDisplayState.high}</span>
                <span>Medium: {activeDisplayState.medium}</span>
                <span>Low: {activeDisplayState.low}</span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="inspector-actions-box">
              <button 
                className="btn-hero-primary"
                onClick={() => {
                  onSelectState && onSelectState(activeDisplayState.state);
                  onNavigateToTab && onNavigateToTab('explorer');
                }}
              >
                <span>Inspect Flagged Works in {activeDisplayState.state}</span>
                <ArrowRight size={14} />
              </button>
              <button 
                className="btn-hero-secondary"
                onClick={() => {
                  setConstituencyStateFilter(activeDisplayState.state);
                  setActiveSubTab('constituencies');
                }}
              >
                <span>View Full Table in {activeDisplayState.state}</span>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* STATE DEEP DIVE: PARLIAMENTARY CONSTITUENCIES & DISTRICT BREAKDOWN */}
        <div className="state-constituencies-deepdive" style={{ marginTop: '20px', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Building size={18} color="#2563eb" />
                <h3 style={{ margin: 0, fontSize: '17px', fontWeight: '800', color: '#0f172a' }}>
                  {activeDisplayState.state} — Parliamentary Constituencies & Seats
                </h3>
              </div>
              <p style={{ margin: '4px 0 0 0', fontSize: '12.5px', color: '#64748b' }}>
                MPLADS performance, MP allocations, and tri-detector anomaly candidates across seats in {activeDisplayState.state}.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#475569', background: '#f1f5f9', padding: '4px 12px', borderRadius: '6px' }}>
                {PARLIAMENTARY_CONSTITUENCIES.filter(c => normalizeName(c.state) === normalizeName(activeDisplayState.state)).length} Listed Seats
              </span>
              <a 
                href="https://mplads.gov.in/" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ fontSize: '12px', fontWeight: '600', color: '#166534', background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '4px 12px', borderRadius: '6px', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <span>Verify on mplads.gov.in</span>
                <ExternalLink size={11} />
              </a>
            </div>
          </div>

          {/* Seat Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px' }}>
            {PARLIAMENTARY_CONSTITUENCIES.filter(c => normalizeName(c.state) === normalizeName(activeDisplayState.state)).length > 0 ? (
              PARLIAMENTARY_CONSTITUENCIES.filter(c => normalizeName(c.state) === normalizeName(activeDisplayState.state)).map(c => (
                <div 
                  key={c.id} 
                  style={{ 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '8px', 
                    padding: '14px', 
                    background: '#f8fafc',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <strong style={{ fontSize: '14px', color: '#0f172a' }}>{c.name}</strong>
                      <span className={`risk-badge badge-${c.risk.toLowerCase()}`} style={{ fontSize: '10px', padding: '2px 6px' }}>
                        {c.risk}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: '#2563eb', marginBottom: '10px' }}>
                      <User size={12} />
                      <span style={{ fontWeight: '600' }}>{c.mp}</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', background: '#ffffff', padding: '8px 10px', borderRadius: '6px', border: '1px solid #e2e8f0', marginBottom: '10px' }}>
                      <div>
                        <div style={{ fontSize: '10.5px', color: '#64748b' }}>Total Works</div>
                        <div style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>{c.total_works}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10.5px', color: '#64748b' }}>Sanctioned</div>
                        <div style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>₹{c.sanctioned_cr} Cr</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10.5px', color: '#64748b' }}>Flagged Anom.</div>
                        <div style={{ fontSize: '13px', fontWeight: '700', color: c.candidates > 20 ? '#dc2626' : '#2563eb' }}>
                          {c.candidates} works
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '10.5px', color: '#64748b' }}>Seat Code</div>
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#475569' }}>{c.id}</div>
                      </div>
                    </div>

                    <div style={{ fontSize: '11px', color: '#475569', marginBottom: '10px', lineHeight: '1.4' }}>
                      <strong style={{ color: '#0f172a' }}>Detector Flag:</strong> {c.top_signal}
                    </div>
                  </div>

                  <button 
                    className="btn-inspect-action"
                    style={{ width: '100%', justifyContent: 'center', padding: '6px 12px' }}
                    onClick={() => {
                      onSelectState && onSelectState(c.state);
                      onNavigateToTab && onNavigateToTab('explorer');
                    }}
                  >
                    <span>Audit {c.name} Works</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              ))
            ) : (
              <div style={{ gridColumn: '1 / -1', padding: '24px', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px dashed #cbd5e1' }}>
                <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>
                  All canonical records for <strong>{activeDisplayState.state}</strong> are indexed in the National Works Database.
                </p>
                <button 
                  className="btn-hero-primary" 
                  style={{ marginTop: '12px', display: 'inline-flex' }}
                  onClick={() => {
                    onSelectState && onSelectState(activeDisplayState.state);
                    onNavigateToTab && onNavigateToTab('explorer');
                  }}
                >
                  <span>Explore All Works in {activeDisplayState.state}</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            )}
          </div>
        </div>
        </>
      )}

      {/* SUB-VIEW 2: LIVE LEAFLET GEO MAP */}
      {activeSubTab === 'leaflet' && (
        <div className="map-view-grid">
          <div className="map-canvas-card">
            <div className="map-controls-bar">
              <span className="ctrl-label">Live OpenStreetMap / CartoDB Tile Projection:</span>
              {selectedState && selectedState !== 'ALL' && (
                <button 
                  className="btn-reset-map-filter"
                  onClick={() => onSelectState && onSelectState('ALL')}
                >
                  Clear Selection ({selectedState})
                </button>
              )}
            </div>
            <IndiaLeafletMap 
              statesData={safeStates} 
              selectedState={selectedState} 
              onSelectState={onSelectState} 
            />
          </div>

          <div className="map-inspector-card">
            <div className="inspector-header">
              <div className="inspector-title-wrap">
                <span className="inspector-eyebrow">State Forensic Triage</span>
                <h2 className="inspector-state-name">{activeDisplayState.state}</h2>
              </div>
              <span className="inspector-rate-badge">
                {activeDisplayState.rate}% Anomaly Rate
              </span>
            </div>

            <div className="inspector-metrics-grid">
              <div className="insp-metric-tile">
                <span className="insp-lbl">Investigation Candidates</span>
                <span className="insp-val text-danger">{activeDisplayState.candidates.toLocaleString()}</span>
                <span className="insp-sub">Tri-detector consensus</span>
              </div>
              <div className="insp-metric-tile">
                <span className="insp-lbl">Total Analyzed Works</span>
                <span className="insp-val">{activeDisplayState.total_works.toLocaleString()}</span>
                <span className="insp-sub">Canonical MPLADS records</span>
              </div>
            </div>

            <div className="inspector-actions-box">
              <button 
                className="btn-hero-primary"
                onClick={() => {
                  onSelectState && onSelectState(activeDisplayState.state);
                  onNavigateToTab && onNavigateToTab('explorer');
                }}
              >
                <span>Inspect Flagged Works in {activeDisplayState.state}</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SUB-VIEW 3: PARLIAMENTARY CONSTITUENCIES EXPLORER */}
      {activeSubTab === 'constituencies' && (
        <div className="constituencies-view-card">
          {/* Filter and Search Bar */}
          <div className="explorer-filter-card">
            <div className="filter-row-top">
              <div className="explorer-search-input">
                <Search size={15} color="#64748b" />
                <input 
                  type="text"
                  placeholder="Search Constituency Name, Member of Parliament, State..."
                  value={constituencySearch}
                  onChange={(e) => setConstituencySearch(e.target.value)}
                />
              </div>

              <div className="filter-dropdowns-group">
                <div className="select-wrap">
                  <span className="select-label">Filter State:</span>
                  <select 
                    value={constituencyStateFilter}
                    onChange={(e) => setConstituencyStateFilter(e.target.value)}
                  >
                    <option value="ALL">All States/UTs ({uniqueStatesList.length})</option>
                    {uniqueStatesList.map(st => (
                      <option key={st} value={st}>{st}</option>
                    ))}
                  </select>
                </div>

                <div className="select-wrap">
                  <span className="select-label">Risk Severity:</span>
                  <select 
                    value={constituencyRiskFilter}
                    onChange={(e) => setConstituencyRiskFilter(e.target.value)}
                  >
                    <option value="ALL">All Risk Tiers</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>

                {(constituencySearch || constituencyStateFilter !== 'ALL' || constituencyRiskFilter !== 'ALL') && (
                  <button 
                    className="btn-reset-filters"
                    onClick={() => {
                      setConstituencySearch('');
                      setConstituencyStateFilter('ALL');
                      setConstituencyRiskFilter('ALL');
                    }}
                  >
                    Reset Filters
                  </button>
                )}
              </div>
            </div>

            <div className="filter-summary-row">
              <span className="records-count-text">
                Showing <strong>{filteredConstituencies.length}</strong> Parliamentary Constituencies
              </span>
            </div>
          </div>

          {/* Parliamentary Constituency Data Table */}
          <div className="table-responsive-wrapper">
            <table className="govtech-data-table">
              <thead>
                <tr>
                  <th style={{ width: '180px' }}>Constituency Name</th>
                  <th style={{ width: '160px' }}>State / Union Territory</th>
                  <th style={{ width: '180px' }}>Member of Parliament (MP)</th>
                  <th style={{ width: '100px' }}>Total Works</th>
                  <th style={{ width: '120px' }}>Flagged Candidates</th>
                  <th style={{ width: '120px' }}>Sanctioned (Cr)</th>
                  <th style={{ width: '100px' }}>Risk Tier</th>
                  <th>Primary Detector Flag</th>
                  <th style={{ width: '110px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredConstituencies.map((c) => (
                  <tr key={c.id} className="table-data-row">
                    <td>
                      <div className="location-cell">
                        <strong className="state-text">{c.name}</strong>
                        <span className="constituency-text">Seat Code: {c.id}</span>
                      </div>
                    </td>
                    <td>
                      <span className="state-text">{c.state}</span>
                    </td>
                    <td>
                      <div className="mp-cell">
                        <User size={12} color="#2563eb" style={{ display: 'inline', marginRight: '4px' }} />
                        <span className="mp-text">{c.mp}</span>
                      </div>
                    </td>
                    <td>
                      <span className="score-mono">{c.total_works}</span>
                    </td>
                    <td>
                      <span className="score-mono" style={{ color: c.candidates > 25 ? '#dc2626' : '#2563eb', fontWeight: 'bold' }}>
                        {c.candidates} works
                      </span>
                    </td>
                    <td>
                      <span className="score-mono">₹{c.sanctioned_cr} Cr</span>
                    </td>
                    <td>
                      <span className={`risk-badge badge-${c.risk.toLowerCase()}`}>
                        {c.risk}
                      </span>
                    </td>
                    <td>
                      <span className="desc-text" style={{ fontSize: '11.5px', color: '#475569' }}>
                        {c.top_signal}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        className="btn-inspect-action"
                        onClick={() => {
                          onSelectState && onSelectState(c.state);
                          onNavigateToTab && onNavigateToTab('explorer');
                        }}
                      >
                        <span>Inspect</span>
                        <ExternalLink size={11} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
