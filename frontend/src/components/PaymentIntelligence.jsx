import { CreditCard, CheckCircle2, TrendingUp, Users, FileSpreadsheet, Info } from 'lucide-react';
import { NATIONAL_OVERVIEW_DEFAULTS } from '../data/indiaStateData.js';

export default function PaymentIntelligence({ overview }) {
  const data = { ...NATIONAL_OVERVIEW_DEFAULTS, ...overview };
  const totalWorks = data.unique_works_analyzed || 104517;
  const worksWithPayments = data.works_with_payments || 54984;
  const worksWithoutPayments = data.works_without_payments || 49533;
  const paymentCoverage = data.payment_coverage_percent || (Number(worksWithPayments) / totalWorks * 100).toFixed(2);
  const withoutCoverage = (100 - Number(paymentCoverage)).toFixed(2);

  const paymentStats = [
    {
      label: 'Works with Payments',
      value: Number(worksWithPayments).toLocaleString(),
      subtext: `${paymentCoverage}% of total works`,
      accent: 'emerald',
      barPct: Math.min(Number(paymentCoverage), 100)
    },
    {
      label: 'Works without Payments',
      value: Number(worksWithoutPayments).toLocaleString(),
      subtext: `${withoutCoverage}% sanction-only works`,
      accent: 'slate',
      barPct: Math.min(Number(withoutCoverage), 100)
    },
    {
      label: 'Total Transactions',
      value: Number(data.payment_transactions).toLocaleString(),
      subtext: 'Recorded vendor payments',
      accent: 'blue',
      barPct: 100
    },
    {
      label: 'Completion Records',
      value: Number(data.completion_records).toLocaleString(),
      subtext: 'Physical works reported complete',
      accent: 'cyan',
      barPct: 32.18
    }
  ];

  const concentrationMetrics = [
    {
      title: 'Works with Multiple Payments',
      count: Number(data.works_multiple_payments).toLocaleString(),
      desc: 'Schemes with ≥ 2 sequential payment disbursements recorded'
    },
    {
      title: 'Works with 5+ Payments',
      count: Number(data.works_5plus_payments).toLocaleString(),
      desc: 'High transaction frequency schemes requiring milestone verification'
    },
    {
      title: 'Works with 10+ Payments',
      count: Number(data.works_10plus_payments).toLocaleString(),
      desc: 'Upper-percentile disbursal density works across Indian constituencies'
    },
    {
      title: 'Works with 5+ Vendors',
      count: Number(data.works_5plus_vendors).toLocaleString(),
      desc: 'Multi-entity executing agency allocations for single work master ID'
    },
    {
      title: 'Works with 10+ Vendors',
      count: Number(data.works_10plus_vendors).toLocaleString(),
      desc: 'Extreme vendor fragmentation pattern identified by analytical screening'
    }
  ];

  return (
    <section className="dashboard-section" id="section-payments">
      <div className="section-header-block">
        <div className="section-title-wrap">
          <h2 className="section-main-heading">Data & Payment Intelligence</h2>
        </div>
      </div>

      <div className="payment-intel-grid">
        {/* Coverage Highlights Column */}
        <div className="payment-coverage-card">
          <div className="panel-subhead">
            <CreditCard size={15} />
            <span>Payment Coverage & Transaction Base</span>
          </div>

          <div className="coverage-metrics-stack">
            {paymentStats.map((stat, idx) => (
              <div key={idx} className="coverage-stat-box">
                <div className="stat-top-row">
                  <span className="stat-label-text">{stat.label}</span>
                  <span className="stat-val-text">{stat.value}</span>
                </div>
                <div className="stat-progress-track">
                  <div 
                    className={`stat-progress-bar bar-${stat.accent}`}
                    style={{ width: `${stat.barPct}%` }}
                  />
                </div>
                <span className="stat-subtext-note">{stat.subtext}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Transaction & Vendor Concentration Column */}
        <div className="payment-concentration-card">
          <div className="panel-subhead">
            <Users size={15} />
            <span>Disbursal Density & Vendor Concentration</span>
          </div>

          <div className="concentration-items-list">
            {concentrationMetrics.map((item, idx) => (
              <div key={idx} className="concentration-row-item">
                <div className="concentration-info-left">
                  <span className="concentration-item-name">{item.title}</span>
                  <span className="concentration-item-desc">{item.desc}</span>
                </div>
                <span className="concentration-badge-num">{item.count}</span>
              </div>
            ))}
          </div>

          <div className="concentration-footer-disclaimer">
            <Info size={12} color="#94a3b8" style={{ flexShrink: 0 }} />
            <span>
              Transaction count and vendor dispersion metrics represent objective analytical attributes from official transaction logs, not proof of irregularity.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
