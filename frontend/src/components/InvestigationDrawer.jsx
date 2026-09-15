import { useEffect, useState } from 'react';
import { 
  X, 
  ShieldAlert, 
  Sparkles, 
  DollarSign, 
  Clock, 
  Layers, 
  AlertTriangle,
  Info,
  Building2,
  Copy,
  Check,
  Scale,
  FileSpreadsheet,
  FileCheck2,
  FileText,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

export default function InvestigationDrawer({
  work,
  explanation,
  open,
  onClose,
  loading,
  onGenerateAI,
  generatingAI
}) {
  const [copied, setCopied] = useState(false);
  const [activeDrawerTab, setActiveDrawerTab] = useState('ai'); // 'ai' | 'financial' | 'timeline' | 'raw'

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && open) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const handleCopyId = () => {
    if (work?.work_id) {
      navigator.clipboard.writeText(String(work.work_id));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined || val === '' || isNaN(Number(val))) return 'Not available';
    return `₹${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  };

  const formatRatio = (val) => {
    if (val === null || val === undefined || val === '' || isNaN(Number(val))) return 'Not available';
    return `${Number(val).toFixed(2)}×`;
  };

  const parseJsonArray = (val) => {
    if (Array.isArray(val)) return val;
    if (typeof val === 'string') {
      try {
        const parsed = JSON.parse(val);
        if (Array.isArray(parsed)) return parsed;
      } catch {
        return [val];
      }
    }
    return [];
  };

  const identity = work?.identity || {};
  const risk = work?.risk || {};
  const financial = work?.financial || {};
  const transactions = work?.transactions || {};
  const timeline = work?.timeline || {};
  const peer = work?.peer_comparison || {};
  const quality = work?.data_quality || {};
  const investigation = work?.investigation || {};
  const ai = explanation || work?.ai_explanation || null;

  const riskLevel = String(risk.final_risk_level || work?.final_risk_level || 'LOW').toUpperCase();
  const rawScore = risk.hybrid_risk_score ?? work?.hybrid_risk_score;
  const scoreVal = rawScore != null ? Number(rawScore).toFixed(1) : '—';
  const qualityTier = risk.data_quality_tier || work?.data_quality_tier || (quality.missing_field_count === 0 ? 'HIGH' : (quality.missing_field_count === 1 ? 'MEDIUM' : 'LOW'));
  const peerSufficient = risk.peer_data_sufficient !== undefined ? risk.peer_data_sufficient : ((peer.peer_count ?? 15) >= 10);

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-top-bar">
          <div className="drawer-header-left">
            <div className="drawer-title-row">
              <span className="drawer-id-badge">#{work?.work_id || 'N/A'}</span>
              <button className="btn-copy-id" onClick={handleCopyId} title="Copy Work ID">
                {copied ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                <span>{copied ? 'Copied' : 'Copy ID'}</span>
              </button>
              <span className={`drawer-risk-badge risk-${riskLevel.toLowerCase()}`}>
                {riskLevel} RISK
              </span>
              <span className="drawer-priority-badge">{priority}</span>
              <span className="sig-badge" style={{ background: '#f1f5f9', color: '#334155', fontWeight: '600' }} title="Data Quality Tier">
                Quality: {qualityTier}
              </span>
              <span className="sig-badge" style={{ background: peerSufficient ? '#f0fdf4' : '#fffbeb', color: peerSufficient ? '#166534' : '#b45309', fontWeight: '600' }} title="Peer Cohort Sufficiency (>=10 Works)">
                {peerSufficient ? '✓ Peer Data ≥10' : '⚠️ Peer Data <10'}
              </span>
            </div>
            <div className="drawer-loc-text">
              {identity.state_name || work?.state_name} • {identity.constituency || work?.constituency} (MP: {identity.mp_name || work?.mp_name})
            </div>
          </div>

          <button className="btn-drawer-close" onClick={onClose} aria-label="Close Drawer">
            <X size={18} />
          </button>
        </div>

        {/* Drawer Navigation Tabs */}
        <div className="drawer-nav-tabs">
          <button 
            className={`d-tab-btn ${activeDrawerTab === 'ai' ? 'd-tab-active' : ''}`}
            onClick={() => setActiveDrawerTab('ai')}
          >
            <Sparkles size={13} />
            <span>AI Reasoning & Findings</span>
          </button>
          <button 
            className={`d-tab-btn ${activeDrawerTab === 'financial' ? 'd-tab-active' : ''}`}
            onClick={() => setActiveDrawerTab('financial')}
          >
            <DollarSign size={13} />
            <span>Financial & Vendors</span>
          </button>
          <button 
            className={`d-tab-btn ${activeDrawerTab === 'timeline' ? 'd-tab-active' : ''}`}
            onClick={() => setActiveDrawerTab('timeline')}
          >
            <Clock size={13} />
            <span>Timeline & Dates</span>
          </button>
          <button 
            className={`d-tab-btn ${activeDrawerTab === 'raw' ? 'd-tab-active' : ''}`}
            onClick={() => setActiveDrawerTab('raw')}
          >
            <FileText size={13} />
            <span>Raw Evidence JSON</span>
          </button>
        </div>

        {/* Drawer Scrollable Content */}
        <div className="drawer-body">
          {loading ? (
            <div className="drawer-loading-box">
              <span className="loading-spinner" />
              <span>Loading complete forensic dossier...</span>
            </div>
          ) : (
            <>
              {/* Tab 1: AI Reasoning & Findings */}
              {activeDrawerTab === 'ai' && (
                <div className="drawer-tab-pane">
                  {/* AI Explanation Box */}
                  <div className="ai-dossier-box">
                    <div className="ai-box-header">
                      <div className="ai-header-left">
                        <Sparkles size={16} color="#16a34a" />
                        <span className="ai-header-title">LLM Investigation Reasoning</span>
                      </div>
                      <button 
                        className="btn-regen-ai"
                        onClick={() => onGenerateAI && onGenerateAI(work?.work_id)}
                        disabled={generatingAI}
                      >
                        <RefreshCw size={12} className={generatingAI ? 'spin-anim' : ''} />
                        <span>{generatingAI ? 'Analyzing...' : 'Regenerate AI'}</span>
                      </button>
                    </div>

                    {ai ? (
                      <div className="ai-content-flow">
                        <div className="ai-section">
                          <span className="ai-section-label">Risk Summary:</span>
                          <p className="ai-summary-text">{ai.risk_summary || 'No summary available.'}</p>
                        </div>

                        {ai.why_flagged && (
                          <div className="ai-section">
                            <span className="ai-section-label">Why This Work Was Flagged:</span>
                            <p className="ai-body-text">{ai.why_flagged}</p>
                          </div>
                        )}

                        {ai.observed_signals && parseJsonArray(ai.observed_signals).length > 0 && (
                          <div className="ai-section">
                            <span className="ai-section-label">Observed Statistical & Rule Signals:</span>
                            <ul className="ai-signals-list">
                              {parseJsonArray(ai.observed_signals).map((sig, i) => (
                                <li key={i}><AlertTriangle size={12} color="#dc2626" /><span>{sig}</span></li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {ai.what_to_verify && parseJsonArray(ai.what_to_verify).length > 0 && (
                          <div className="ai-section checklist-section">
                            <span className="ai-section-label">Investigator Field Verification Checklist:</span>
                            <ul className="ai-checklist">
                              {parseJsonArray(ai.what_to_verify).map((item, i) => (
                                <li key={i}><Check size={13} color="#16a34a" /><span>{item}</span></li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="ai-empty-prompt">
                        <p>No cached AI explanation for this work. Click below to trigger real-time LLM reasoning.</p>
                        <button 
                          className="btn-hero-primary"
                          onClick={() => onGenerateAI && onGenerateAI(work?.work_id)}
                          disabled={generatingAI}
                          style={{ marginTop: '12px' }}
                        >
                          <Sparkles size={14} />
                          <span>Generate Real-time AI Explanation</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Tri-Detector Scoring Breakdown */}
                  <div className="drawer-card">
                    <h4 className="drawer-card-title"><Layers size={15} color="#2563eb" /> Detector Engine Breakdown</h4>
                    <div className="drawer-score-grid">
                      <div className="score-tile">
                        <span className="score-tile-label">Hybrid Risk Score</span>
                        <span className="score-tile-val big-score">{scoreVal}</span>
                        <span className="score-tile-sub">{riskLevel} Severity</span>
                      </div>
                      <div className="score-tile">
                        <span className="score-tile-label">Rule Score</span>
                        <span className="score-tile-val">{risk.rule_score ?? work?.rule_score ?? '—'}</span>
                        <span className="score-tile-sub">Deterministic Rules</span>
                      </div>
                      <div className="score-tile">
                        <span className="score-tile-label">Statistical Score</span>
                        <span className="score-tile-val">{risk.statistical_score ?? work?.statistical_score ?? '—'}</span>
                        <span className="score-tile-sub">Peer Cohort IQR</span>
                      </div>
                      <div className="score-tile">
                        <span className="score-tile-label">ML Score</span>
                        <span className="score-tile-val">{risk.ml_score ?? work?.ml_score ?? '—'}</span>
                        <span className="score-tile-sub">Isolation Forest</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Financial & Vendors */}
              {activeDrawerTab === 'financial' && (
                <div className="drawer-tab-pane">
                  <div className="drawer-card">
                    <h4 className="drawer-card-title"><DollarSign size={15} color="#059669" /> Financial Allocations & Outflows</h4>
                    <div className="financial-data-grid">
                      <div className="fin-row"><span className="fin-lbl">Recommended Amount:</span><span className="fin-val">{formatCurrency(financial.recommended_amount ?? work?.recommended_amount)}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Sanctioned Amount:</span><span className="fin-val fin-bold">{formatCurrency(financial.sanction_amount ?? work?.sanction_amount)}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Reported Actual Expenditure:</span><span className="fin-val">{formatCurrency(financial.actual_amount ?? work?.actual_amount)}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Recorded Fund Disbursement:</span><span className="fin-val fin-bold">{formatCurrency(financial.total_fund_disbursed ?? work?.total_fund_disbursed)}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Disbursed to Sanction Ratio:</span><span className="fin-val">{formatRatio(financial.disbursed_to_sanction_ratio ?? work?.disbursed_to_sanction_ratio)}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Peer Group Median Sanction:</span><span className="fin-val">{formatCurrency(peer.peer_median_sanction ?? work?.peer_median_sanction)}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Sanction to Peer Median Ratio:</span><span className="fin-val fin-danger">{formatRatio(peer.sanction_to_peer_median ?? work?.sanction_to_peer_median)}</span></div>
                    </div>
                    <div style={{ marginTop: '10px', padding: '8px 10px', background: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '11px', color: '#64748b', lineHeight: '1.4' }}>
                      <strong style={{ color: '#334155' }}>Methodology Note:</strong> Peer groups match works within the same State & Category. Statistical baselines do not account for micro-regional terrain difficulty or district-level construction cost index variations.
                    </div>
                  </div>

                  <div className="drawer-card">
                    <h4 className="drawer-card-title"><Building2 size={15} color="#4f46e5" /> Vendor & Transaction Structure</h4>
                    <div className="financial-data-grid">
                      <div className="fin-row"><span className="fin-lbl">Payment Transaction Count:</span><span className="fin-val">{transactions.payment_count ?? work?.payment_count ?? '—'}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Unique Vendor Count:</span><span className="fin-val">{transactions.unique_vendor_count ?? work?.unique_vendor_count ?? '—'}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Payments per 30 Days (Velocity):</span><span className="fin-val">{transactions.payments_per_30_days ?? work?.payments_per_30_days ?? '—'}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Work Stage / Status:</span><span className="fin-val">{work?.work_stage || 'Not specified'}</span></div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Timeline & Dates */}
              {activeDrawerTab === 'timeline' && (
                <div className="drawer-tab-pane">
                  <div className="drawer-card">
                    <h4 className="drawer-card-title"><Clock size={15} color="#d97706" /> Project Implementation Dates</h4>
                    <div className="financial-data-grid">
                      <div className="fin-row"><span className="fin-lbl">Recommendation Date:</span><span className="fin-val">{timeline.recommendation_date || work?.recommendation_date || 'Not recorded'}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Sanction Date:</span><span className="fin-val">{timeline.sanction_date || work?.sanction_date || 'Not recorded'}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Reported Completion Duration:</span><span className="fin-val">{timeline.completion_duration_days ? `${timeline.completion_duration_days} days` : 'Not recorded'}</span></div>
                      <div className="fin-row"><span className="fin-lbl">Payments After Reported Completion:</span><span className="fin-val fin-danger">{timeline.payment_after_completion_days ? `${timeline.payment_after_completion_days} days` : 'None'}</span></div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Raw JSON */}
              {activeDrawerTab === 'raw' && (
                <div className="drawer-tab-pane">
                  <div className="drawer-card">
                    <h4 className="drawer-card-title"><FileText size={15} color="#64748b" /> Raw Metadata & Evidence Object</h4>
                    <pre className="raw-json-viewer">
                      {JSON.stringify(work, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
