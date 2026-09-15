import { 
  ShieldCheck, 
  Scale, 
  Cpu, 
  Workflow, 
  CheckCircle2, 
  Layers, 
  AlertTriangle,
  FileCheck
} from 'lucide-react';

export default function DetectorEngineView({ summary }) {
  const allThree = summary?.detector_agreement?.all_three ?? 597;
  const twoMethods = summary?.detector_agreement?.two_methods ?? 2473;
  const oneMethod = summary?.detector_agreement?.one_method ?? 4451;
  const totalCandidates = summary?.total_investigation_candidates ?? 7521;

  const engines = [
    {
      id: 'rule',
      title: '1. Deterministic Rule-Based Engine',
      weight: '35% Score Weight',
      icon: Scale,
      color: 'blue',
      description: 'Audits statutory compliance, financial integrity boundaries, milestone progression, and procurement structure constraints.',
      rules: [
        'Sanctioned works with zero recorded disbursements after 180+ days',
        'Actual expenditure exceeding sanctioned administrative ceiling',
        'High vendor concentration (>10 vendors on single minor work)',
        'Payment activity occurring after reported completion date',
        'Work recommendation without recorded administrative sanction'
      ]
    },
    {
      id: 'stat',
      title: '2. Statistical Peer-Group Benchmark (IQR)',
      weight: '35% Score Weight',
      icon: Cpu,
      color: 'indigo',
      description: 'Calculates hierarchical peer medians (State → Category → Activity) and identifies extreme cost ratios and z-score outliers.',
      rules: [
        'Sanction amount exceeding 3× peer-group median allocation',
        'Interquartile Range (IQR) upper whisker boundary violations',
        'Payment pacing velocity outliers (>50 transactions per 30 days)',
        'Disbursement-to-sanction ratio statistical distribution skew',
        'Hierarchical peer fallback when local activity cohort is small'
      ]
    },
    {
      id: 'ml',
      title: '3. Unsupervised Isolation Forest ML',
      weight: '30% Score Weight',
      icon: Workflow,
      color: 'emerald',
      description: '98-dimensional engineered feature vectors evaluated with ensemble tree partitioning to isolate multi-variable anomalies.',
      rules: [
        'Multi-variate interaction between vendor count, sanction, and pacing',
        'Anomaly scoring percentile calculated across national dataset',
        'Log-transformed financial ratios and disbursement curves',
        'Tree partition depth scoring for high-dimensional isolation',
        'Unsupervised detection without requiring labeled historic fraud'
      ]
    }
  ];

  return (
    <div className="view-container">
      <div className="view-header-row">
        <div>
          <h1 className="view-main-title">Tri-Detector Architecture & Consensus Engine</h1>
          <p className="view-sub-title">
            FundGuard AI eliminates single-detector false positives by synthesizing deterministic rules, statistical peer cohorts, and machine learning into a hybrid risk index.
          </p>
        </div>
      </div>

      {/* Consensus Summary Banner */}
      <div className="consensus-summary-card">
        <div className="consensus-top">
          <div className="consensus-badge">
            <Layers size={14} color="#1d4ed8" />
            <span>Consensus Agreement Matrix</span>
          </div>
          <span className="consensus-total">Total Flagged: {totalCandidates.toLocaleString()} Works</span>
        </div>

        <div className="consensus-bars-grid">
          <div className="consensus-bar-item">
            <div className="bar-label-row">
              <span className="bar-title">All 3 Engines Agree (Critical Consensus)</span>
              <span className="bar-val crit-text">{allThree.toLocaleString()} works ({((allThree / totalCandidates) * 100).toFixed(1)}%)</span>
            </div>
            <div className="meter-track">
              <div className="meter-fill-bar bar-crit" style={{ width: `${(allThree / totalCandidates) * 100}%` }} />
            </div>
            <span className="bar-sub">Strongest anomaly signal — highest investigation priority</span>
          </div>

          <div className="consensus-bar-item">
            <div className="bar-label-row">
              <span className="bar-title">2 Engines Agree (Moderate Consensus)</span>
              <span className="bar-val high-text">{twoMethods.toLocaleString()} works ({((twoMethods / totalCandidates) * 100).toFixed(1)}%)</span>
            </div>
            <div className="meter-track">
              <div className="meter-fill-bar bar-high" style={{ width: `${(twoMethods / totalCandidates) * 100}%` }} />
            </div>
            <span className="bar-sub">Corroborated signal across two independent analytical methodologies</span>
          </div>

          <div className="consensus-bar-item">
            <div className="bar-label-row">
              <span className="bar-title">1 Engine Signal (Screening Tier)</span>
              <span className="bar-val blue-text">{oneMethod.toLocaleString()} works ({((oneMethod / totalCandidates) * 100).toFixed(1)}%)</span>
            </div>
            <div className="meter-track">
              <div className="meter-fill-bar bar-blue" style={{ width: `${(oneMethod / totalCandidates) * 100}%` }} />
            </div>
            <span className="bar-sub">Isolated anomaly flag requiring secondary corroboration</span>
          </div>
        </div>
      </div>

      {/* 3 Detector Deep Dives */}
      <div className="detector-cards-grid">
        {engines.map((eng) => {
          const Icon = eng.icon;
          return (
            <div key={eng.id} className={`detector-engine-card eng-${eng.color}`}>
              <div className="eng-header">
                <div className="eng-icon-circle">
                  <Icon size={18} />
                </div>
                <div>
                  <h3 className="eng-title">{eng.title}</h3>
                  <span className="eng-weight">{eng.weight}</span>
                </div>
              </div>
              <p className="eng-desc">{eng.description}</p>
              <div className="eng-rules-box">
                <span className="rules-heading">Key Detection Signals:</span>
                <ul className="rules-list">
                  {eng.rules.map((r, i) => (
                    <li key={i}>
                      <CheckCircle2 size={12} color="#16a34a" />
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
