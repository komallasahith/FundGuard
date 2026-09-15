import { Database, FileSpreadsheet, MapPin, Users, CreditCard, CheckCircle2 } from 'lucide-react';

export default function NationalOverview({ overview, loading, error, onRetry }) {
  if (loading) {
    return (
      <section className="dashboard-section" id="section-national-overview">
        <div className="section-header-block">
          <div className="section-title-wrap">
            <h2 className="section-main-heading">National Overview</h2>
          </div>
        </div>
        <div className="section-loading-box">
          <span className="loading-spinner" />
          <span>Loading National Overview...</span>
        </div>
      </section>
    );
  }

  if (error && !overview) {
    return (
      <section className="dashboard-section" id="section-national-overview">
        <div className="section-header-block">
          <div className="section-title-wrap">
            <h2 className="section-main-heading">National Overview</h2>
          </div>
        </div>
        <div className="section-error-box">
          <span>Failed to load national overview.</span>
          {onRetry && (
            <button className="btn-retry" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      </section>
    );
  }

  const rawRecords = overview?.source_records_collected;
  const totalWorks = overview?.unique_works_analyzed;
  const statesCovered = overview?.states_and_uts_covered;
  const mpMappings = overview?.mp_constituency_mappings;
  const paymentTxns = overview?.payment_transactions;
  const completionRecords = overview?.completion_records;
  const paymentCoverage = overview?.payment_coverage_percent;

  const cards = [
    {
      id: 'raw-records',
      label: 'Source Records Collected',
      value: rawRecords != null ? Number(rawRecords).toLocaleString() : 'Not available',
      subtitle: 'Raw expenditure & milestone records',
      icon: Database,
      accent: 'cyan'
    },
    {
      id: 'unique-works',
      label: 'Works Analyzed',
      value: totalWorks != null ? Number(totalWorks).toLocaleString() : 'Not available',
      subtitle: 'Canonical MPLADS scheme master items',
      icon: FileSpreadsheet,
      accent: 'blue'
    },
    {
      id: 'states-covered',
      label: 'States / UTs',
      value: statesCovered != null ? `${statesCovered} States / UTs` : 'Not available',
      subtitle: 'Complete national geographic coverage',
      icon: MapPin,
      accent: 'emerald'
    },
    {
      id: 'mp-mappings',
      label: 'MP–Constituency Mappings',
      value: mpMappings != null ? Number(mpMappings).toLocaleString() : 'Not available',
      subtitle: 'Lok Sabha & Rajya Sabha allocations',
      icon: Users,
      accent: 'cyan'
    },
    {
      id: 'payments',
      label: 'Payment Transactions',
      value: paymentTxns != null ? Number(paymentTxns).toLocaleString() : 'Not available',
      subtitle: paymentCoverage != null ? `${paymentCoverage}% payment coverage` : 'Electronic disbursals',
      icon: CreditCard,
      accent: 'amber'
    },
    {
      id: 'completions',
      label: 'Completion Records',
      value: completionRecords != null ? Number(completionRecords).toLocaleString() : 'Not available',
      subtitle: 'Physical works reported finished',
      icon: CheckCircle2,
      accent: 'emerald'
    }
  ];

  return (
    <section className="dashboard-section" id="section-national-overview">
      <div className="section-header-block">
        <div className="section-title-wrap">
          <h2 className="section-main-heading">National Overview</h2>
        </div>
      </div>

      <div className="metrics-grid six-columns">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.id} className={`metric-tile tile-${card.accent}`}>
              <div className="metric-top">
                <span className="metric-tag">{card.label}</span>
                <div className="metric-icon-wrap">
                  <Icon size={15} />
                </div>
              </div>
              <div className="metric-number">{card.value}</div>
              <div className="metric-subtitle">{card.subtitle}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
