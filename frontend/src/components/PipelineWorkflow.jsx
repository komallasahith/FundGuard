import { Sparkles } from 'lucide-react';

export default function PipelineWorkflow() {
  const stages = [
    {
      num: '01',
      tag: 'Ingestion',
      title: 'MPLADS Source Data',
      detail: '297,398 raw records collected across 36 States/UTs'
    },
    {
      num: '02',
      tag: 'Curation',
      title: 'Validation & Master Index',
      detail: '104,517 canonical works with validated ID resolution'
    },
    {
      num: '03',
      tag: 'Telemetry',
      title: 'Feature Engineering',
      detail: 'Disbursal ratios, vendor dispersion, IQR boundaries'
    },
    {
      num: '04',
      tag: 'Detection',
      title: 'Parallel Tri-Engine',
      detail: 'Rule (40%) + Statistical (30%) + ML (30%) independent detection'
    },
    {
      num: '05',
      tag: 'Synthesis',
      title: 'Hybrid Risk & Evidence',
      detail: 'Consensus score (0–100) + factual evidence compilation'
    },
    {
      num: '06',
      tag: 'Triage',
      title: 'Investigation Queue',
      detail: 'Prioritized casefile review & human verification by auditors'
    }
  ];

  return (
    <section className="dashboard-section" id="section-pipeline">
      <div className="section-header-block">
        <div className="section-title-wrap">
          <h2 className="section-main-heading">How FundGuard AI Works</h2>
        </div>
      </div>

      <div className="pipeline-workflow-card">
        {/* Pipeline Stage Blocks */}
        <div className="pipeline-stages-container">
          {stages.map((st) => (
            <div key={st.num} className="pipeline-stage-step">
              <div className="stage-num-badge">{st.num}</div>
              <div className="stage-card-box">
                <span className="stage-tag">{st.tag}</span>
                <span className="stage-title">{st.title}</span>
                <span className="stage-detail">{st.detail}</span>
              </div>
            </div>
          ))}
        </div>

        {/* AI Layer Clarification Callout */}
        <div className="ai-layer-clarification-banner">
          <div className="ai-clarify-left">
            <Sparkles size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <span className="ai-clarify-title">On-Demand AI Reasoning Layer: </span>
              <span className="ai-clarify-text">
                Risk scoring and candidate selection are computed exclusively by deterministic rules and statistical engines. Large language models (LLMs) do not determine risk scores; they provide optional on-demand case explanations strictly from compiled evidence.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
