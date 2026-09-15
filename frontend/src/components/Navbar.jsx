import { 
  ShieldCheck, 
  LayoutDashboard, 
  BarChart3, 
  Map, 
  Database, 
  Layers, 
  CreditCard, 
  RefreshCw,
  AlertTriangle,
  FileSearch,
  Sparkles
} from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  summary,
  health,
  overview,
  onRefresh,
  reloading
}) {
  const totalWorks = health?.records?.total_works ?? 104517;
  const candidatesCount = summary?.total_investigation_candidates ?? 7521;
  const criticalCount = summary?.risk_distribution?.critical ?? 1668;
  const allThreeCount = summary?.detector_agreement?.all_three ?? 597;

  const navTabs = [
    { id: 'overview', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'analytics', label: 'Visual Analytics & Charts', icon: BarChart3, badge: '6 Charts' },
    { id: 'map', label: 'Geo-Spatial India Map', icon: Map, badge: '36 States/UTs' },
    { id: 'explorer', label: 'All Works & Anomaly Explorer', icon: Database, badge: candidatesCount.toLocaleString() },
    { id: 'detectors', label: 'Tri-Detector Engine', icon: Layers, badge: `${allThreeCount} Strong` },
    { id: 'payments', label: 'Payment Intelligence', icon: CreditCard, badge: '82k Txns' }
  ];

  return (
    <header className="govtech-header">
      {/* Top Banner with Brand & Telemetry */}
      <div className="govtech-top-banner">
        <div className="header-brand-group">
          <div className="govtech-shield-logo">
            <ShieldCheck size={22} color="#ffffff" />
          </div>
          <div className="brand-text-block">
            <div className="brand-title-row">
              <span className="brand-main-title">FUNDGUARD AI</span>
              <span className="gov-badge">GOVT OF INDIA • MPLADS</span>
            </div>
            <span className="brand-sub-title">
              National Financial Intelligence & Multi-Detector Anomaly Detection Platform
            </span>
          </div>
        </div>

        {/* Live Telemetry & KPI Chips */}
        <div className="header-telemetry-group">
          <a 
            href="https://mplads.gov.in/" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="telemetry-chip live-status" 
            style={{ textDecoration: 'none', cursor: 'pointer' }}
            title="Open Official Ministry of Statistics and Programme Implementation MPLADS Portal"
          >
            <span className="pulsing-green-dot" />
            <span className="telemetry-text">Official MPLADS Portal (mplads.gov.in)</span>
          </a>

          <div className="telemetry-chip">
            <span className="chip-label">Raw Collected Records:</span>
            <span className="chip-val">{Number(overview?.source_records_collected ?? 297398).toLocaleString()}</span>
          </div>

          <div className="telemetry-chip">
            <span className="chip-label">Works Audited:</span>
            <span className="chip-val">{totalWorks.toLocaleString()}</span>
          </div>

          <div className="telemetry-chip alert-chip">
            <AlertTriangle size={12} color="#b91c1c" />
            <span className="chip-label">Flagged Candidates:</span>
            <span className="chip-val chip-danger">{candidatesCount.toLocaleString()}</span>
          </div>

          <button 
            className="btn-sync" 
            onClick={onRefresh} 
            disabled={reloading}
            title="Reload dataset & re-run aggregations"
          >
            <RefreshCw size={13} className={reloading ? 'spin-anim' : ''} />
            <span>{reloading ? 'Syncing...' : 'Sync Data'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Tab Bar */}
      <nav className="govtech-nav-bar">
        <div className="nav-tabs-scroll">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                className={`nav-tab-btn ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={15} />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className={`tab-badge ${isActive ? 'badge-active' : ''}`}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
