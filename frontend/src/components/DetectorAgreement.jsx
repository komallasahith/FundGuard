import { Layers, ShieldCheck, Cpu, Scale, ChevronRight, Filter } from 'lucide-react';

export default function DetectorAgreement({ 
  summary, 
  selectedAgreement, 
  onSelectAgreement 
}) {
  const allThree = summary?.detector_agreement?.all_three ?? 0;
  const twoMethods = summary?.detector_agreement?.two_methods ?? 0;
  const oneMethod = summary?.detector_agreement?.one_method ?? 0;
  const total = allThree + twoMethods + oneMethod || (summary?.total_investigation_candidates ?? 1);

  const agreementCards = [
    {
      id: 'ALL 3 METHODS',
      tag: 'Maximum Consensus',
      title: 'All 3 Methods',
      count: allThree,
      pct: ((allThree / total) * 100).toFixed(1),
      desc: 'Simultaneous flags by Rule Engine + Statistical IQR + Isolation Forest ML.',
      badgeClass: 'badge-crit',
      filterVal: 'ALL 3'
    },
    {
      id: 'TWO METHODS',
      tag: 'Dual Engine Overlap',
      title: 'Two Methods',
      count: twoMethods,
      pct: ((twoMethods / total) * 100).toFixed(1),
      desc: 'Corroborated by two independent screening mechanisms.',
      badgeClass: 'badge-high',
      filterVal: 'TWO'
    },
    {
      id: 'ONE METHOD',
      tag: 'Single Engine Signal',
      title: 'One Method',
      count: oneMethod,
      pct: ((oneMethod / total) * 100).toFixed(1),
      desc: 'Triggered by a dedicated single detector (e.g. extreme statistical peer deviation).',
      badgeClass: 'badge-med',
      filterVal: 'ONE'
    }
  ];

  return (
    <section className="dashboard-section" id="section-detectors">
      <div className="section-header-block">
        <div className="section-title-wrap">
          <h2 className="section-main-heading">Detector Agreement</h2>
        </div>
        <div className="section-meta-pill">
          <span>Formula: Hybrid = 0.40(Rule) + 0.30(Statistical) + 0.30(ML)</span>
        </div>
      </div>

      <div className="detector-agreement-grid">
        {/* Consensus Breakdown Cards */}
        <div className="agreement-cards-stack">
          {agreementCards.map((card) => {
            const isSelected = selectedAgreement === card.filterVal;
            return (
              <div 
                key={card.id}
                className={`agreement-row-card ${isSelected ? 'active-filter' : ''}`}
                onClick={() => onSelectAgreement(card.filterVal)}
                role="button"
                tabIndex={0}
                title={`Filter queue by ${card.title}`}
              >
                <div className="agreement-row-left">
                  <div className="agreement-count-box">
                    <span className="agreement-big-num">{card.count.toLocaleString()}</span>
                    <span className="agreement-pct-text">{card.pct}% of flags</span>
                  </div>
                  <div className="agreement-details-wrap">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <span className="agreement-card-title">{card.title}</span>
                      <span className={`agreement-pill ${card.badgeClass}`}>{card.tag}</span>
                    </div>
                    <p className="agreement-desc-text">{card.desc}</p>
                  </div>
                </div>
                
                <div className="agreement-action-col">
                  {isSelected ? (
                    <span className="filter-active-pill">
                      <Filter size={11} />
                      Filter Active
                    </span>
                  ) : (
                    <span className="filter-hover-hint">
                      Filter Queue
                      <ChevronRight size={12} />
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* The 3 Analytical Methods Deep Dive Card */}
        <div className="detector-methods-deepdive-card">
          <div className="deepdive-header">
            <Layers size={15} />
            <span className="deepdive-title">Three Independent Detection Methods</span>
          </div>

          <div className="method-items-list">
            <div className="method-item">
              <div className="method-badge">
                Rule Engine (40%)
              </div>
              <div className="method-info">
                <span className="method-name">Deterministic Policy Engine</span>
                <span className="method-desc">
                  Identifies objective statutory boundary violations, sanction vs actual expenditure discrepancies, and timeline milestone inversions.
                </span>
              </div>
            </div>

            <div className="method-item">
              <div className="method-badge">
                Statistical (30%)
              </div>
              <div className="method-info">
                <span className="method-name">Statistical Deviation Engine</span>
                <span className="method-desc">
                  Calculates robust Interquartile Range (IQR) bounds and peer group median cost ratios across comparable works in the same state/category.
                </span>
              </div>
            </div>

            <div className="method-item">
              <div className="method-badge">
                ML Model (30%)
              </div>
              <div className="method-info">
                <span className="method-name">Isolation Forest ML Engine</span>
                <span className="method-desc">
                  Unsupervised ensemble anomaly tree isolation identifying multi-dimensional outliers in payment transaction density and patterns.
                </span>
              </div>
            </div>
          </div>

          <div className="deepdive-footer-note">
            <span>
              Detector agreement measures the convergence of independent analytical mechanisms, distinguishing isolated single-metric anomalies from multi-vector flags.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
