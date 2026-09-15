import { 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { ShieldAlert, Layers } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #cbd5e1',
        padding: '8px 12px',
        borderRadius: '3px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '11px',
        boxShadow: '0 2px 8px rgba(15, 23, 42, 0.08)'
      }}>
        <div style={{ color: '#475569', marginBottom: '2px', fontWeight: 600 }}>{label || data.name}</div>
        <div style={{ color: data.payload.color || '#0f172a', fontWeight: 700 }}>
          {Number(data.value).toLocaleString()} candidate works
        </div>
      </div>
    );
  }
  return null;
};

export default function RiskOverview({ summary }) {
  const critical = summary?.risk_distribution?.critical ?? 0;
  const high = summary?.risk_distribution?.high ?? 0;
  const medium = summary?.risk_distribution?.medium ?? 0;
  const low = summary?.risk_distribution?.low ?? 0;

  const allThree = summary?.detector_agreement?.all_three ?? 0;
  const twoMethods = summary?.detector_agreement?.two_methods ?? 0;
  const oneMethod = summary?.detector_agreement?.one_method ?? 0;

  const riskBarData = [
    { name: 'CRITICAL', count: critical, color: '#dc2626' },
    { name: 'HIGH', count: high, color: '#ea580c' },
    { name: 'MEDIUM', count: medium, color: '#ca8a04' },
    { name: 'LOW', count: low, color: '#16a34a' }
  ];

  const agreementData = [
    { name: 'All 3 Detectors', value: allThree, color: '#0284c7' },
    { name: '2 Detectors Overlap', value: twoMethods, color: '#ca8a04' },
    { name: 'Single Detector', value: oneMethod, color: '#7c3aed' }
  ].filter(item => item.value > 0 || (allThree === 0 && twoMethods === 0 && oneMethod === 0));

  return (
    <div className="analytics-grid" id="section-risk">
      {/* Risk Distribution Chart Panel */}
      <div className="tactical-panel">
        <div className="panel-header">
          <div className="panel-title-wrap">
            <span className="panel-kicker">CLASSIFICATION DISTRIBUTION</span>
            <h3 className="panel-title">Risk Severity Spectrum</h3>
          </div>
          <ShieldAlert size={16} color="#dc2626" />
        </div>
        
        <div className="chart-content">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={riskBarData} margin={{ top: 15, right: 10, left: -15, bottom: 0 }}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="#94a3b8" 
                tick={{ fontSize: 10, fontFamily: "'JetBrains Mono', monospace", fill: '#475569' }} 
              />
              <YAxis 
                stroke="#94a3b8" 
                tick={{ fontSize: 10, fontFamily: "'JetBrains Mono', monospace", fill: '#475569' }} 
                scale="sqrt"
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                {riskBarData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-legend-row">
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#dc2626' }} />
            <span>Critical: {critical.toLocaleString()}</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#ea580c' }} />
            <span>High: {high.toLocaleString()}</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#ca8a04' }} />
            <span>Medium: {medium.toLocaleString()}</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#16a34a' }} />
            <span>Low: {low.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Consensus Agreement Doughnut Panel */}
      <div className="tactical-panel">
        <div className="panel-header">
          <div className="panel-title-wrap">
            <span className="panel-kicker">CROSS-DETECTOR OVERLAP</span>
            <h3 className="panel-title">Detector Agreement</h3>
          </div>
          <Layers size={16} color="#0284c7" />
        </div>

        <div className="chart-content">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={agreementData.length > 0 ? agreementData : [{ name: 'Pending', value: 1, color: '#e2e8f0' }]}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={4}
                dataKey="value"
              >
                {(agreementData.length > 0 ? agreementData : [{ name: 'Pending', value: 1, color: '#e2e8f0' }]).map((entry, index) => (
                  <Cell key={`donut-${index}`} fill={entry.color} stroke="#ffffff" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-legend-row">
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#0284c7' }} />
            <span>All 3 Detectors: {allThree.toLocaleString()}</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#ca8a04' }} />
            <span>2 Detectors: {twoMethods.toLocaleString()}</span>
          </div>
          <div className="legend-item">
            <span className="legend-color-pip" style={{ backgroundColor: '#7c3aed' }} />
            <span>1 Detector: {oneMethod.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Tri-Engine Risk Formula Overview */}
      <div className="tactical-panel" id="section-detectors">
        <div className="panel-header">
          <div className="panel-title-wrap">
            <span className="panel-kicker">DETECTION ARCHITECTURE</span>
            <h3 className="panel-title">Hybrid Engine Matrix</h3>
          </div>
          <span className="badge-agreement strong">40% / 30% / 30%</span>
        </div>

        <div className="detector-cards-stack">
          <div className="detector-row-card">
            <div className="detector-info-left">
              <div className="detector-indicator-box">
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: '11px' }}>RUL</span>
              </div>
              <div className="detector-text">
                <span className="detector-name">Deterministic Rule Engine</span>
                <span className="detector-desc">Policy boundaries, sanction vs expenditure mismatch</span>
              </div>
            </div>
            <span className="detector-weight-pill">40% WT</span>
          </div>

          <div className="detector-row-card">
            <div className="detector-info-left">
              <div className="detector-indicator-box" style={{ color: '#ca8a04' }}>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: '11px' }}>STA</span>
              </div>
              <div className="detector-text">
                <span className="detector-name">Statistical Deviation Engine</span>
                <span className="detector-desc">Peer median cost ratio, distribution z-scores</span>
              </div>
            </div>
            <span className="detector-weight-pill" style={{ color: '#ca8a04' }}>30% WT</span>
          </div>

          <div className="detector-row-card">
            <div className="detector-info-left">
              <div className="detector-indicator-box" style={{ color: '#7c3aed' }}>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: '11px' }}>ML</span>
              </div>
              <div className="detector-text">
                <span className="detector-name">Isolation Forest ML Engine</span>
                <span className="detector-desc">Unsupervised multi-dimensional anomaly isolation</span>
              </div>
            </div>
            <span className="detector-weight-pill" style={{ color: '#7c3aed' }}>30% WT</span>
          </div>
        </div>

        <div className="consensus-footer-banner">
          <span>CONSENSUS FORMULA:</span>
          <span style={{ color: '#0f172a', fontWeight: 700 }}>HYBRID = 0.40(R) + 0.30(S) + 0.30(ML)</span>
        </div>
      </div>
    </div>
  );
}


