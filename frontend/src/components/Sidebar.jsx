import { 
  LayoutDashboard, 
  Map, 
  ShieldAlert, 
  Layers, 
  CreditCard, 
  Workflow, 
  FileSearch, 
  Building2,
  Database,
  CheckCircle2
} from 'lucide-react';

export default function Sidebar({ 
  activeNav, 
  setActiveNav, 
  mobileOpen, 
  setMobileOpen,
  summary,
  health
}) {
  const totalWorks = health?.records?.total_works ?? 104517;
  const investigationCandidates = summary?.total_investigation_candidates ?? 7521;
  const criticalCount = summary?.risk_distribution?.critical ?? 1668;
  const allThreeCount = summary?.detector_agreement?.all_three ?? 597;

  const navItems = [
    { id: 'national-overview', label: 'National Overview', icon: LayoutDashboard },
    { id: 'map', label: 'India State Map', icon: Map, tag: '36 States/UTs' },
    { id: 'intelligence', label: 'Investigation Intelligence', icon: ShieldAlert, count: investigationCandidates },
    { id: 'detectors', label: 'Detector Agreement', icon: Layers, count: allThreeCount },
    { id: 'payments', label: 'Payment Intelligence', icon: CreditCard },
    { id: 'pipeline', label: 'How FundGuard Works', icon: Workflow },
    { id: 'queue', label: 'Investigation Queue', icon: FileSearch, count: investigationCandidates },
    { id: 'provenance', label: 'Source Provenance', icon: Building2 }
  ];

  const handleNavClick = (id) => {
    setActiveNav(id);
    if (setMobileOpen) setMobileOpen(false);

    const sectionId = id === 'queue' ? 'investigation-queue-section' : `section-${id}`;
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-nav-container">
        <div className="nav-section-tag">Investigation Sections</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => handleNavClick(item.id)}
            >
              <Icon size={14} />
              <span>{item.label}</span>
              {item.count !== undefined && (
                <span className="nav-counter">{item.count.toLocaleString()}</span>
              )}
              {item.tag && (
                <span className="nav-counter" style={{ color: '#38bdf8', borderColor: '#0284c7' }}>{item.tag}</span>
              )}
            </button>
          );
        })}

        <div className="nav-section-tag" style={{ marginTop: '16px' }}>Dataset Metrics</div>
        <div className="sidebar-nav-item static-nav-item">
          <Database size={14} color="#94a3b8" />
          <span>Works Analyzed</span>
          <span className="nav-counter">{totalWorks.toLocaleString()}</span>
        </div>
        <div className="sidebar-nav-item static-nav-item">
          <CheckCircle2 size={14} color="#10b981" />
          <span>Coverage Scope</span>
          <span className="nav-counter" style={{ color: '#10b981' }}>36 States / UTs</span>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="system-telemetry-box">
          <div className="telemetry-row">
            <span className="telemetry-label">Methodology:</span>
            <span className="telemetry-value" style={{ color: '#38bdf8' }}>Detector Agreement</span>
          </div>
          <div className="telemetry-row">
            <span className="telemetry-label">Detectors:</span>
            <span className="telemetry-value">Rule / Stat / ML</span>
          </div>
          <div className="telemetry-row">
            <span className="telemetry-label">Works Analyzed:</span>
            <span className="telemetry-value">{totalWorks.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
