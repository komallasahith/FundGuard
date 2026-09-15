import { 
  Database, 
  FileSpreadsheet, 
  MapPin, 
  Users, 
  CreditCard, 
  CheckCircle2, 
  ShieldAlert, 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  CheckCircle,
  ArrowRight,
  Sparkles,
  Layers,
  Scale
} from 'lucide-react';

export default function OverviewView({ 
  overview, 
  summary, 
  onSelectRisk, 
  onNavigateToTab 
}) {
  const rawRecords = overview?.source_records_collected ?? 297398;
  const totalWorks = overview?.unique_works_analyzed ?? 104517;
  const statesCovered = overview?.states_and_uts_covered ?? 36;
  const mpMappings = overview?.mp_constituency_mappings ?? 529;
  const paymentTxns = overview?.payment_transactions ?? 82320;
  const completionRecords = overview?.completion_records ?? 33630;
  const paymentCoverage = overview?.payment_coverage_percent ?? 52.61;

  const totalCandidates = summary?.total_investigation_candidates ?? 7521;
  const critical = summary?.risk_distribution?.critical ?? 684;
  const high = summary?.risk_distribution?.high ?? 1302;
  const medium = summary?.risk_distribution?.medium ?? 2415;
  const low = summary?.risk_distribution?.low ?? 3120;
  const allThree = summary?.detector_agreement?.all_three ?? 597;
  const twoMethods = summary?.detector_agreement?.two_methods ?? 2473;
  const oneMethod = summary?.detector_agreement?.one_method ?? 4451;

  const kpiCards = [
    {
      label: 'Source Records Collected',
      value: rawRecords.toLocaleString(),
      sub: 'Official MOSPI portal transaction records',
      icon: Database,
      accent: 'blue'
    },
    {
      label: 'Unique Works Analyzed',
      value: totalWorks.toLocaleString(),
      sub: 'Canonical MPLADS scheme master items',
      icon: FileSpreadsheet,
      accent: 'indigo'
    },
    {
      label: 'States & UTs Covered',
      value: `${statesCovered} States/UTs`,
      sub: 'Complete nationwide geographic scope',
      icon: MapPin,
      accent: 'emerald'
    },
    {
      label: 'MP–Constituency Mappings',
      value: mpMappings.toLocaleString(),
      sub: 'Lok Sabha & Rajya Sabha allocations',
      icon: Users,
      accent: 'blue'
    },
    {
      label: 'Payment Transactions',
      value: paymentTxns.toLocaleString(),
      sub: `${paymentCoverage}% electronic coverage`,
      icon: CreditCard,
      accent: 'amber'
    },
    {
      label: 'Completion Milestones',
      value: completionRecords.toLocaleString(),
      sub: 'Physical works reported finished',
      icon: CheckCircle2,
      accent: 'emerald'
    }
  ];

  const riskTiers = [
    {
      id: 'ALL',
      name: 'All Flagged Candidates',
      count: totalCandidates.toLocaleString(),
      pct: `${((totalCandidates / totalWorks) * 100).toFixed(1)}% of total`,
      desc: 'Prioritized investigation queue',
      tag: 'Any Detector Signal',
      color: 'blue',
      icon: ShieldAlert
    },
    {
      id: 'CRITICAL',
      name: 'Critical Risk Candidates',
      count: critical.toLocaleString(),
      pct: 'Consensus OR Score ≥ 90.4',
      desc: 'Multi-detector severe anomalies — guaranteed for consensus works',
      tag: 'Priority P1 — 9%',
      color: 'crit',
      icon: AlertTriangle
    },
    {
      id: 'HIGH',
      name: 'High Risk Candidates',
      count: high.toLocaleString(),
      pct: 'Hybrid Score 56.5–90.4',
      desc: 'Substantial financial or peer deviation',
      tag: 'Priority P2 — 17%',
      color: 'high',
      icon: AlertCircle
    },
    {
      id: 'MEDIUM',
      name: 'Medium Risk Candidates',
      count: medium.toLocaleString(),
      pct: 'Hybrid Score 35.0–56.5',
      desc: 'Notable implementation pattern anomaly',
      tag: 'Priority P3 — 32%',
      color: 'med',
      icon: Info
    },
    {
      id: 'LOW',
      name: 'Low Risk / Single-Signal',
      count: low.toLocaleString(),
      pct: 'Hybrid Score 0.1–35.0',
      desc: 'Single detector screening signal',
      tag: 'Priority P4 — 41%',
      color: 'low',
      icon: CheckCircle
    }
  ];

  // Score histogram data — 5-point bins
  const scoreHistData = [
    { bin: '0-5',   count: 0 },
    { bin: '5-10',  count: 0 },
    { bin: '10-15', count: 0 },
    { bin: '15-20', count: 14 },
    { bin: '20-25', count: 52 },
    { bin: '25-30', count: 1547 },
    { bin: '30-35', count: 1507 },
    { bin: '35-40', count: 1286 },
    { bin: '40-45', count: 700 },
    { bin: '45-50', count: 429 },
    { bin: '50-55', count: 0 },
    { bin: '55-60', count: 0 },
    { bin: '60-65', count: 0 },
    { bin: '65-70', count: 0 },
    { bin: '70-75', count: 0 },
    { bin: '75-80', count: 0 },
    { bin: '80-85', count: 0 },
    { bin: '85-90', count: 0 },
    { bin: '90-95', count: 679 },
    { bin: '95-100', count: 5 },
  ];
  const histMax = Math.max(...scoreHistData.map(d => d.count));

  // Tier color by bin range
  const getBinColor = (bin) => {
    const lo = parseInt(bin.split('-')[0], 10);
    if (lo >= 90) return 'var(--crit-accent, #dc2626)';
    if (lo >= 57) return 'var(--high-accent, #ea580c)';
    if (lo >= 35) return 'var(--med-accent, #ca8a04)';
    if (lo > 0)   return 'var(--low-accent, #16a34a)';
    return '#94a3b8';
  };

  return (
    <div className="view-container">
      {/* Welcome & System Architecture Hero Banner */}
      <div className="executive-hero-card">
        <div className="hero-content-left">
          <div className="hero-pill-badge">
            <Sparkles size={13} color="#2563eb" />
            <span>AI-Powered Financial Intelligence Platform</span>
          </div>
          <h1 className="hero-heading">
            MPLADS Implementation & Expenditure Monitoring System
          </h1>
          <p className="hero-description">
            FundGuard AI combines deterministic statutory rules, peer-group statistical distribution benchmarks (IQR), and unsupervised Isolation Forest machine learning with LLM-powered factual reasoning to prioritize works requiring human investigation.
          </p>
          <div className="hero-actions-row">
            <button 
              className="btn-hero-primary"
              onClick={() => onNavigateToTab('explorer')}
            >
              <span>Explore Investigation Queue ({totalCandidates.toLocaleString()})</span>
              <ArrowRight size={14} />
            </button>
            <button 
              className="btn-hero-secondary"
              onClick={() => onNavigateToTab('analytics')}
            >
              <span>View Interactive Analytics & Charts</span>
            </button>
          </div>
        </div>

        <div className="hero-summary-box">
          <div className="hero-metric-header">Detection Consensus Breakdown</div>
          <div className="hero-stat-row">
            <span className="stat-label">All 3 Engines Agree (Critical):</span>
            <span className="stat-badge crit-badge">{allThree.toLocaleString()} works</span>
          </div>
          <div className="hero-stat-row">
            <span className="stat-label">2 Engines Agree (Moderate):</span>
            <span className="stat-badge high-badge">{twoMethods.toLocaleString()} works</span>
          </div>
          <div className="hero-stat-row">
            <span className="stat-label">1 Engine Signal (Screening):</span>
            <span className="stat-badge single-badge">{oneMethod.toLocaleString()} works</span>
          </div>
          <div className="hero-stat-row total-row">
            <span className="stat-label">Total Works in National Index:</span>
            <span className="stat-val-bold">{totalWorks.toLocaleString()} works</span>
          </div>
        </div>
      </div>

      {/* National Telemetry KPI Tiles */}
      <div className="section-block">
        <div className="section-title-wrap">
          <h2 className="section-title">National Telemetry & Data Coverage</h2>
          <span className="section-subtitle">Aggregated metrics from 36 States & Union Territories</span>
        </div>
        <div className="kpi-grid">
          {kpiCards.map((kpi, idx) => {
            const Icon = kpi.icon;
            return (
              <div key={idx} className={`kpi-card accent-${kpi.accent}`}>
                <div className="kpi-top">
                  <span className="kpi-label">{kpi.label}</span>
                  <div className="kpi-icon-circle">
                    <Icon size={16} />
                  </div>
                </div>
                <div className="kpi-value">{kpi.value}</div>
                <div className="kpi-sub">{kpi.sub}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Risk Tiers Grid */}
      <div className="section-block">
        <div className="section-title-wrap">
          <h2 className="section-title">Investigation Risk Classification</h2>
          <span className="section-subtitle">Click any tier to inspect works in the Anomaly Explorer</span>
        </div>
        <div className="risk-tiers-grid">
          {riskTiers.map((tier) => {
            const Icon = tier.icon;
            return (
              <div 
                key={tier.id}
                className={`risk-tier-card tier-${tier.color}`}
                onClick={() => {
                  onSelectRisk(tier.id);
                  onNavigateToTab('explorer');
                }}
              >
                <div className="tier-top">
                  <span className="tier-tag">{tier.tag}</span>
                  <div className="tier-icon-wrap">
                    <Icon size={16} />
                  </div>
                </div>
                <div className="tier-count">{tier.count}</div>
                <div className="tier-name">{tier.name}</div>
                <div className="tier-pct">{tier.pct}</div>
                <div className="tier-desc">{tier.desc}</div>
                <div className="tier-action-hint">
                  <span>Inspect Tier</span>
                  <ArrowRight size={12} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Hybrid Risk Score Distribution Histogram */}
      <div className="section-block">
        <div className="section-title-wrap">
          <h2 className="section-title">Hybrid Risk Score Distribution</h2>
          <span className="section-subtitle">
            Score histogram across all 104,517 works — color-coded by investigation tier
          </span>
        </div>
        <div className="score-histogram-card">
          <div className="hist-legend-row">
            <span className="hist-legend-item"><span className="hist-dot" style={{background:'#dc2626'}}></span>P1 Critical (≥90.4 or consensus)</span>
            <span className="hist-legend-item"><span className="hist-dot" style={{background:'#ea580c'}}></span>P2 High (56.5–90.4)</span>
            <span className="hist-legend-item"><span className="hist-dot" style={{background:'#ca8a04'}}></span>P3 Medium (35–56.5)</span>
            <span className="hist-legend-item"><span className="hist-dot" style={{background:'#16a34a'}}></span>P4 Low (0.1–35)</span>
            <span className="hist-legend-item"><span className="hist-dot" style={{background:'#94a3b8'}}></span>No Signal</span>
          </div>
          <div className="hist-bars-row">
            {scoreHistData.map((d) => {
              const barHeight = histMax > 0 ? Math.max((d.count / histMax) * 140, d.count > 0 ? 4 : 0) : 0;
              const color = getBinColor(d.bin);
              return (
                <div key={d.bin} className="hist-bar-col" title={`Score ${d.bin}: ${d.count.toLocaleString()} works`}>
                  <div className="hist-bar-wrap">
                    <div
                      className="hist-bar"
                      style={{ height: `${barHeight}px`, background: color }}
                    />
                  </div>
                  <span className="hist-bar-label">{d.bin.split('-')[0]}</span>
                </div>
              );
            })}
          </div>
          <div className="hist-footnote">
            Bimodal structure: the central cluster (20–50) reflects the majority of MPLADS works with moderate evidence;
            the right spike (90–100) is the P1 critical tier driven by score + consensus override.
          </div>
        </div>
      </div>

      {/* Statutory Disclaimer Box */}
      <div className="statutory-disclaimer-card">
        <div className="disclaimer-header">
          <Info size={16} color="#1d4ed8" />
          <span className="disclaimer-title">Statutory Screening & Audit Disclaimer</span>
        </div>
        <p className="disclaimer-text">
          FundGuard AI is an automated screening and risk-prioritization system for the Members of Parliament Local Area Development Scheme (MPLADS). Flagged works represent candidates prioritized for administrative review and field verification, not conclusive determinations of irregularity, corruption, or wrongdoing. All findings must be corroborated against original sanction orders, measurement books, and physical inspection records.
        </p>
      </div>
    </div>
  );
}
