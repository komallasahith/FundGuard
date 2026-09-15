import { ShieldAlert, AlertTriangle, AlertCircle, CheckCircle, Info, Filter } from 'lucide-react';

export default function InvestigationIntelligence({ 
  summary, 
  selectedRisk, 
  onSelectRisk 
}) {
  const totalCandidates = summary?.total_investigation_candidates;
  const critical = summary?.risk_distribution?.critical;
  const high = summary?.risk_distribution?.high;
  const medium = summary?.risk_distribution?.medium;
  const low = summary?.risk_distribution?.low;

  const riskCards = [
    {
      id: 'ALL',
      name: 'All Candidates',
      count: totalCandidates != null ? totalCandidates.toLocaleString() : 'Loading...',
      threshold: 'Any Detector Signal',
      tag: 'Total Flagged',
      colorClass: 'cyan',
      icon: ShieldAlert,
      filterVal: 'ALL'
    },
    {
      id: 'CRITICAL',
      name: 'Critical Risk',
      count: critical != null ? critical.toLocaleString() : 'Loading...',
      threshold: 'Hybrid Score ≥ 60.0',
      tag: 'Priority P1 Candidate',
      colorClass: 'crit',
      icon: AlertTriangle,
      filterVal: 'CRITICAL'
    },
    {
      id: 'HIGH',
      name: 'High Risk',
      count: high != null ? high.toLocaleString() : 'Loading...',
      threshold: 'Hybrid Score 40.0 – 59.9',
      tag: 'Priority P2 Candidate',
      colorClass: 'high',
      icon: AlertCircle,
      filterVal: 'HIGH'
    },
    {
      id: 'MEDIUM',
      name: 'Medium Risk',
      count: medium != null ? medium.toLocaleString() : 'Loading...',
      threshold: 'Hybrid Score 20.0 – 39.9',
      tag: 'Priority P3 Candidate',
      colorClass: 'med',
      icon: Info,
      filterVal: 'MEDIUM'
    },
    {
      id: 'LOW',
      name: 'Low Risk',
      count: low != null ? low.toLocaleString() : 'Loading...',
      threshold: 'Hybrid Score 0.1 – 19.9',
      tag: 'Single-Signal Tier',
      colorClass: 'low',
      icon: CheckCircle,
      filterVal: 'LOW'
    }
  ];

  return (
    <section className="dashboard-section" id="section-intelligence">
      <div className="section-header-block">
        <div className="section-title-wrap">
          <h2 className="section-main-heading">Investigation Intelligence</h2>
        </div>
        <div className="section-meta-pill">
          <span>Click tier to filter queue</span>
        </div>
      </div>

      <div className="intelligence-cards-grid">
        {riskCards.map((card) => {
          const Icon = card.icon;
          const isSelected = selectedRisk === card.filterVal;
          return (
            <div 
              key={card.id}
              className={`intelligence-card card-${card.colorClass} ${isSelected ? 'active-filter' : ''}`}
              onClick={() => onSelectRisk(card.filterVal)}
              role="button"
              tabIndex={0}
              title={`Filter investigation queue for ${card.name}`}
            >
              <div className="intel-card-top">
                <span className="intel-card-tag">{card.tag}</span>
                <div className="intel-card-icon">
                  <Icon size={14} />
                </div>
              </div>
              <div className="intel-card-num">{card.count}</div>
              <div className="intel-card-title">{card.name}</div>
              <div className="intel-card-sub">{card.threshold}</div>
              
              {isSelected && (
                <div className="intel-card-active-indicator">
                  <Filter size={10} />
                  <span>Filter Active</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Statutory Disclaimer Box */}
      <div className="intelligence-disclaimer-box">
        <div className="disclaimer-title-row">
          <Info size={14} />
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
            Investigation Screening Disclaimer
          </span>
        </div>
        <p className="disclaimer-body-text">
          These are anomaly/risk candidates selected for human investigation. They do not establish fraud, corruption, or wrongdoing. All flagged works require verification of official administrative sanctions, measurement books, and physical milestone reports.
        </p>
      </div>
    </section>
  );
}
