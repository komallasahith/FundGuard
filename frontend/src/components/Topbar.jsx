import { Menu, RefreshCw, AlertTriangle, ShieldCheck, Database, Sun, Moon } from 'lucide-react';

export default function Topbar({ 
  summary, 
  health,
  onRefresh, 
  reloading, 
  setMobileOpen,
  theme = 'grey',
  setTheme
}) {
  const totalWorks = health?.records?.total_works ?? 104517;
  const criticalRisk = summary?.risk_distribution?.critical ?? 1668;
  const candidatesCount = summary?.total_investigation_candidates ?? 7521;

  const toggleTheme = () => {
    if (setTheme) {
      setTheme(prev => prev === 'dark' ? 'grey' : 'dark');
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button 
          className="mobile-toggle-btn"
          onClick={() => setMobileOpen(prev => !prev)}
          aria-label="Toggle Navigation Menu"
        >
          <Menu size={16} />
        </button>

        <div className="topbar-brand">
          <div className="topbar-brand-icon">
            <ShieldCheck size={18} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="topbar-brand-name">FUNDGUARD AI</span>
            <span className="topbar-brand-sub">
              India-wide MPLADS Investigation Intelligence
            </span>
          </div>
        </div>

        <div className="classification-badge">
          <Database size={11} />
          <span>36 States / UTs</span>
        </div>
      </div>

      <div className="topbar-right">
        <div className="quick-metric-chip">
          <span className="chip-label">Works:</span>
          <span className="chip-value">{totalWorks.toLocaleString()}</span>
        </div>

        <div className="quick-metric-chip highlight-amber">
          <span className="chip-label">Candidates:</span>
          <span className="chip-value">{candidatesCount.toLocaleString()}</span>
        </div>

        <div className="quick-metric-chip highlight-red">
          <AlertTriangle size={12} color="var(--risk-crit)" />
          <span className="chip-label">Critical:</span>
          <span className="chip-value">{criticalRisk.toLocaleString()}</span>
        </div>

        {setTheme && (
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Grey' : 'Dark'} theme`}
            aria-label="Toggle visual theme"
          >
            {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
            <span>{theme === 'dark' ? 'Grey' : 'Dark'}</span>
          </button>
        )}

        <button 
          className="btn-primary" 
          onClick={onRefresh} 
          disabled={reloading}
          title="Reload dataset & re-run detector aggregations"
        >
          <RefreshCw size={13} className={reloading ? 'spin-anim' : ''} style={reloading ? { animation: 'spin 1s linear infinite' } : {}} />
          <span>{reloading ? 'Syncing...' : 'Refresh'}</span>
        </button>
      </div>
    </header>
  );
}
