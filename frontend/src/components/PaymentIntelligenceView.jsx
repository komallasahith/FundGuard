import { 
  CreditCard, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Users, 
  FileSpreadsheet, 
  Zap,
  TrendingUp,
  Activity
} from 'lucide-react';

export default function PaymentIntelligenceView({ overview }) {
  const paymentTxns = overview?.payment_transactions ?? 82320;
  const worksWithPayments = overview?.works_with_payments ?? 55000;
  const worksWithoutPayments = overview?.works_without_payments ?? 49517;
  const paymentCoverage = overview?.payment_coverage_percent ?? 52.61;

  const paymentStats = [
    {
      title: 'Electronic Transactions',
      val: paymentTxns.toLocaleString(),
      sub: 'PFMS/e-GramSwaraj payment vouchers',
      icon: CreditCard,
      color: 'blue'
    },
    {
      title: 'Electronic Coverage Rate',
      val: `${paymentCoverage}%`,
      sub: 'Sanctioned works with electronic transactions',
      icon: Zap,
      color: 'emerald'
    },
    {
      title: 'Works with Recorded Payments',
      val: worksWithPayments.toLocaleString(),
      sub: 'Works with 1 or more payment vouchers',
      icon: CheckCircle2,
      color: 'indigo'
    },
    {
      title: 'Works Without Payment Records',
      val: worksWithoutPayments.toLocaleString(),
      sub: 'Sanctioned works pending voucher upload',
      icon: Clock,
      color: 'amber'
    }
  ];

  return (
    <div className="view-container">
      <div className="view-header-row">
        <div>
          <h1 className="view-main-title">Payment Intelligence & Electronic Disbursal Audits</h1>
          <p className="view-sub-title">
            Electronic payment voucher tracking, vendor concentration metrics, and disbursement velocity analysis.
          </p>
        </div>
      </div>

      <div className="kpi-grid four-cols">
        {paymentStats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className={`kpi-card accent-${stat.color}`}>
              <div className="kpi-top">
                <span className="kpi-label">{stat.title}</span>
                <div className="kpi-icon-circle">
                  <Icon size={16} />
                </div>
              </div>
              <div className="kpi-value">{stat.val}</div>
              <div className="kpi-sub">{stat.sub}</div>
            </div>
          );
        })}
      </div>

      {/* Forensic Signals Box */}
      <div className="payment-insights-grid">
        <div className="payment-insight-card">
          <div className="insight-card-header">
            <AlertTriangle size={16} color="#c2410c" />
            <h3 className="insight-title">Key Payment Forensic Risk Patterns</h3>
          </div>
          <div className="insight-list">
            <div className="insight-item">
              <strong>Post-Completion Payments:</strong> Flagging payment vouchers recorded 30+ days after official physical milestone completion.
            </div>
            <div className="insight-item">
              <strong>Split Transaction Pacing:</strong> Detecting micro-vouchers split below statutory tendering thresholds to bypass competitive bidding.
            </div>
            <div className="insight-item">
              <strong>Vendor Proliferation:</strong> Flagging single minor community works disbursing payments to more than 15 distinct vendor accounts.
            </div>
            <div className="insight-item">
              <strong>Zero-Disbursement Dormancy:</strong> Identifying sanctioned projects with zero expenditure records 12+ months post-approval.
            </div>
          </div>
        </div>

        <div className="payment-insight-card">
          <div className="insight-card-header">
            <Activity size={16} color="#2563eb" />
            <h3 className="insight-title">Electronic Audit Integration (PFMS)</h3>
          </div>
          <p className="insight-desc">
            FundGuard AI automatically links work recommendation records with electronic PFMS payment voucher streams, reconstructing complete financial histories per work to detect discrepancies between sanctioned amounts and actual ledger outflows.
          </p>
          <div className="audit-flow-box">
            <div className="flow-step">1. Sanction Approval</div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">2. Work Order Issuance</div>
            <div className="flow-arrow">→</div>
            <div className="flow-step">3. PFMS Payment Vouchers</div>
            <div className="flow-arrow">→</div>
            <div className="flow-step active-flow">4. FundGuard AI Audit</div>
          </div>
        </div>
      </div>
    </div>
  );
}
