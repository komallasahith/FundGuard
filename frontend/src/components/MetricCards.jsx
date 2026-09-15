import { 
  Database, 
  AlertTriangle, 
  ShieldAlert, 
  Layers, 
  TrendingUp,
  FileCheck2
} from 'lucide-react';

export default function MetricCards({ summary, health }) {
  const totalAnalyzed = health?.records?.total_works ?? 104517;
  const totalCandidates = summary?.total_investigation_candidates ?? 0;
  const critical = summary?.risk_distribution?.critical ?? 0;
  const high = summary?.risk_distribution?.high ?? 0;
  const medium = summary?.risk_distribution?.medium ?? 0;
  const low = summary?.risk_distribution?.low ?? 0;
  
  const allThree = summary?.detector_agreement?.all_three ?? 0;
  const twoMethods = summary?.detector_agreement?.two_methods ?? 0;
  const consensusTotal = allThree + twoMethods;
  
  const avgScore = summary?.average_hybrid_risk_score !== null && summary?.average_hybrid_risk_score !== undefined
    ? Number(summary.average_hybrid_risk_score).toFixed(2)
    : '—';

  const cards = [
    {
      tag: 'TOTAL WORKS ANALYZED',
      value: totalAnalyzed ? totalAnalyzed.toLocaleString() : '—',
      subtitle: 'All-India MPLADS Works in Database',
      icon: Database,
      tileClass: 'cyan-tile',
      iconColor: '#0f172a'
    },
    {
      tag: 'INVESTIGATION CANDIDATES',
      value: totalCandidates ? totalCandidates.toLocaleString() : '0',
      subtitle: `${critical.toLocaleString()} Critical + ${high.toLocaleString()} High flags`,
      icon: ShieldAlert,
      tileClass: 'risk-high-tile',
      iconColor: '#b91c1c'
    },
    {
      tag: 'CRITICAL RISK TIER',
      value: critical.toLocaleString(),
      subtitle: 'Score ≥ 60 (Requires Priority Verification)',
      icon: AlertTriangle,
      tileClass: 'risk-high-tile',
      iconColor: '#b91c1c'
    },
    {
      tag: 'HIGH & MEDIUM SIGNALS',
      value: `${high.toLocaleString()} / ${medium.toLocaleString()}`,
      subtitle: 'High (≥40) / Medium (≥20) Risk Tiers',
      icon: FileCheck2,
      tileClass: 'risk-med-tile',
      iconColor: '#a16207'
    },
    {
      tag: 'DETECTOR CONSENSUS',
      value: consensusTotal.toLocaleString(),
      subtitle: `${allThree} All-Three + ${twoMethods} Two-Method consensus`,
      icon: Layers,
      tileClass: 'violet-tile',
      iconColor: '#6b21a8'
    },
    {
      tag: 'AVG ANOMALY INDEX',
      value: avgScore !== '—' ? `${avgScore}` : '—',
      subtitle: 'Weighted Hybrid Score / 100',
      icon: TrendingUp,
      tileClass: 'cyan-tile',
      iconColor: '#0f172a'
    }
  ];

  return (
    <section className="metrics-grid" id="section-metrics">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div key={idx} className={`metric-tile ${card.tileClass}`}>
            <div className="metric-top">
              <span className="metric-tag">{card.tag}</span>
              <div className="metric-icon-wrap" style={{ color: card.iconColor }}>
                <Icon size={16} />
              </div>
            </div>
            <div className="metric-number">{card.value}</div>
            <div className="metric-subtitle">{card.subtitle}</div>
          </div>
        );
      })}
    </section>
  );
}

