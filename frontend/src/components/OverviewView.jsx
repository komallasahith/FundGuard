import { useState } from 'react';
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
  const [histMode, setHistMode] = useState('tier'); // 'tier' | 'signal'
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
      pct: '597 Consensus + 87 Score ≥90.4',
      desc: 'All 3-engine consensus works + top dual-engine outliers (90.4 threshold isolates tail)',
      tag: 'Priority P1 — 9.1%',
      color: 'crit',
      icon: AlertTriangle
    },
    {
      id: 'HIGH',
      name: 'High Risk Candidates',
      count: high.toLocaleString(),
      pct: 'Hybrid Score 56.5–90.4',
      desc: 'Substantial financial or peer deviation (1,250 dual-signal, 52 single-signal)',
      tag: 'Priority P2 — 17.3%',
      color: 'high',
      icon: AlertCircle
    },
    {
      id: 'MEDIUM',
      name: 'Medium Risk Candidates',
      count: medium.toLocaleString(),
      pct: 'Hybrid Score 35.0–56.5',
      desc: 'Notable pattern anomaly (1,119 dual-signal, 1,296 single-signal)',
      tag: 'Priority P3 — 32.1%',
      color: 'med',
      icon: Info
    },
    {
      id: 'LOW',
      name: 'Low Risk / Single-Signal',
      count: low.toLocaleString(),
      pct: 'Hybrid Score 0.1–35.0',
      desc: 'Single detector screening signal (3,103 single-signal, 17 dual-signal)',
      tag: 'Priority P4 — 41.5%',
      color: 'low',
      icon: CheckCircle
    }
  ];

  // Score histogram data across 7,521 candidates with signal counts
  const scoreHistData = [
    { bin: '0-5',   total: 0,    s1: 0,    s2: 0,   s3: 0 },
    { bin: '5-10',  total: 0,    s1: 0,    s2: 0,   s3: 0 },
    { bin: '10-15', total: 29,   s1: 29,   s2: 0,   s3: 0 },
    { bin: '15-20', total: 37,   s1: 37,   s2: 0,   s3: 0 },
    { bin: '20-25', total: 202,  s1: 202,  s2: 0,   s3: 0 },
    { bin: '25-30', total: 1233, s1: 1233, s2: 0,   s3: 0 },
    { bin: '30-35', total: 1619, s1: 1602, s2: 17,  s3: 0 },
    { bin: '35-40', total: 534,  s1: 400,  s2: 134, s3: 0 },
    { bin: '40-45', total: 1068, s1: 567,  s2: 501, s3: 0 },
    { bin: '45-50', total: 448,  s1: 241,  s2: 207, s3: 0 },
    { bin: '50-55', total: 262,  s1: 36,   s2: 225, s3: 1 },
    { bin: '55-60', total: 271,  s1: 104,  s2: 135, s3: 32 },
    { bin: '60-65', total: 290,  s1: 0,    s2: 289, s3: 1 },
    { bin: '65-70', total: 661,  s1: 0,    s2: 129, s3: 532 },
    { bin: '70-75', total: 150,  s1: 0,    s2: 119, s3: 31 },
    { bin: '75-80', total: 116,  s1: 0,    s2: 116, s3: 0 },
    { bin: '80-85', total: 69,   s1: 0,    s2: 69,  s3: 0 },
    { bin: '85-90', total: 437,  s1: 0,    s2: 437, s3: 0 },
    { bin: '90-95', total: 95,   s1: 0,    s2: 95,  s3: 0 },
    { bin: '95-100', total: 0,   s1: 0,    s2: 0,   s3: 0 },
  ];
  const histMax = Math.max(...scoreHistData.map(d => d.total));

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
        <div className="section-title-wrap" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="section-title">Hybrid Risk Score Distribution & Signal Overlay</h2>
            <span className="section-subtitle">
              Score histogram across 7,521 prioritized candidates — toggle between triage tiers and underlying detector signal count
            </span>
          </div>
          <div className="hist-toggle-group">
            <button
              type="button"
              className={`hist-toggle-btn ${histMode === 'tier' ? 'active' : ''}`}
              onClick={() => setHistMode('tier')}
            >
              Priority Tiers
            </button>
            <button
              type="button"
              className={`hist-toggle-btn ${histMode === 'signal' ? 'active' : ''}`}
              onClick={() => setHistMode('signal')}
            >
              Signal-Count Overlay
            </button>
          </div>
        </div>
        <div className="score-histogram-card">
          {histMode === 'tier' ? (
            <div className="hist-legend-row">
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#dc2626' }}></span>
                <strong>P1 Critical</strong> (684 works: 597 consensus + 87 score ≥ 90.4)
              </span>
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#ea580c' }}></span>
                <strong>P2 High</strong> (1,302 works: 56.5–90.4)
              </span>
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#ca8a04' }}></span>
                <strong>P3 Medium</strong> (2,415 works: 35.0–56.5)
              </span>
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#16a34a' }}></span>
                <strong>P4 Low</strong> (3,120 works: 0.1–35.0)
              </span>
            </div>
          ) : (
            <div className="hist-legend-row">
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#f43f5e' }}></span>
                <strong>3-Engine Consensus</strong> (597 works — unconditional P1 triage override)
              </span>
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#f59e0b' }}></span>
                <strong>2 Detectors Fired</strong> (2,473 works — spans 30–95; 87 reach P1 via score ≥90.4)
              </span>
              <span className="hist-legend-item">
                <span className="hist-dot" style={{ background: '#38bdf8' }}></span>
                <strong>1 Detector Fired</strong> (4,451 works — single-screening signals, primarily P4)
              </span>
            </div>
          )}

          <div className="hist-bars-row">
            {scoreHistData.map((d) => {
              const totalHeight = histMax > 0 ? Math.max((d.total / histMax) * 140, d.total > 0 ? 4 : 0) : 0;
              const titleText = `Score ${d.bin}: ${d.total.toLocaleString()} works (1-sig: ${d.s1}, 2-sig: ${d.s2}, 3-sig consensus: ${d.s3})`;

              return (
                <div key={d.bin} className="hist-bar-col" title={titleText}>
                  <div className="hist-bar-wrap">
                    {histMode === 'tier' ? (
                      <div
                        className="hist-bar"
                        style={{ height: `${totalHeight}px`, background: getBinColor(d.bin) }}
                      />
                    ) : (
                      <div className="hist-bar-stacked" style={{ height: `${totalHeight}px` }}>
                        {d.s3 > 0 && (
                          <div
                            className="hist-bar-seg"
                            style={{
                              height: `${(d.s3 / d.total) * 100}%`,
                              background: '#f43f5e',
                            }}
                            title={`Consensus (3 signals): ${d.s3}`}
                          />
                        )}
                        {d.s2 > 0 && (
                          <div
                            className="hist-bar-seg"
                            style={{
                              height: `${(d.s2 / d.total) * 100}%`,
                              background: '#f59e0b',
                            }}
                            title={`2 signals: ${d.s2}`}
                          />
                        )}
                        {d.s1 > 0 && (
                          <div
                            className="hist-bar-seg"
                            style={{
                              height: `${(d.s1 / d.total) * 100}%`,
                              background: '#38bdf8',
                            }}
                            title={`1 signal: ${d.s1}`}
                          />
                        )}
                      </div>
                    )}
                  </div>
                  <span className="hist-bar-label">{d.bin.split('-')[0]}</span>
                </div>
              );
            })}
          </div>

          <div className="hist-footnote">
            <strong>Architectural Insight (Option B Calibration)</strong>: 
            The bimodal score profile is structurally driven by independent signal count. 
            All 597 three-engine consensus works cluster at scores 50–75 and are elevated unconditionally to P1 by policy override. 
            The 90.4 score threshold selectively captures the extreme 87 dual-detector outliers that warrant urgent review, while single-signal works naturally form the P4 base (41.5%).
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
