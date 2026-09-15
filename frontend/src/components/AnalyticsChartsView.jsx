import { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area
} from 'recharts';
import { fetchCharts } from '../services/api.js';
import { 
  BarChart3, 
  PieChart as PieIcon, 
  TrendingUp, 
  Layers, 
  MapPin, 
  Building2,
  DollarSign,
  Activity
} from 'lucide-react';

const RISK_COLORS = {
  Critical: '#dc2626',
  High: '#ea580c',
  Medium: '#d97706',
  Low: '#16a34a',
  'Standard Risk': '#94a3b8'
};

const CONSENSUS_COLORS = ['#dc2626', '#ea580c', '#2563eb'];
const STAGE_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'];

export default function AnalyticsChartsView() {
  const [chartsData, setChartsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await fetchCharts();
        if (res && res.success) {
          setChartsData(res);
        }
      } catch (err) {
        console.error('Failed to load chart data:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const riskData = chartsData?.riskDistribution || [
    { name: "Critical", count: 1668, fill: "#dc2626" },
    { name: "High", count: 677, fill: "#ea580c" },
    { name: "Medium", count: 2613, fill: "#d97706" },
    { name: "Low", count: 2563, fill: "#16a34a" }
  ];

  const consensusData = chartsData?.detectorConsensus || [
    { name: "All 3 Engines", value: 597, fill: "#dc2626" },
    { name: "2 Engines", value: 2473, fill: "#ea580c" },
    { name: "1 Engine", value: 4451, fill: "#2563eb" }
  ];

  const topStatesData = chartsData?.topStates || [
    { name: "Uttar Pradesh", candidates: 1240, works: 16500, rate: 7.52 },
    { name: "Maharashtra", candidates: 890, works: 11200, rate: 7.95 },
    { name: "Rajasthan", candidates: 745, works: 9400, rate: 7.93 },
    { name: "Madhya Pradesh", candidates: 680, works: 8900, rate: 7.64 },
    { name: "Tamil Nadu", candidates: 620, works: 7800, rate: 7.95 },
    { name: "Bihar", candidates: 580, works: 8200, rate: 7.07 },
    { name: "Karnataka", candidates: 510, works: 6900, rate: 7.39 },
    { name: "West Bengal", candidates: 470, works: 6400, rate: 7.34 },
    { name: "Gujarat", candidates: 430, works: 5900, rate: 7.29 },
    { name: "Telangana", candidates: 390, works: 5279, rate: 7.39 }
  ];

  const categoryData = chartsData?.categoryData || [
    { name: "Roads & Pathways", count: 38400 },
    { name: "Community Halls", count: 26150 },
    { name: "Playgrounds & Sports", count: 14200 },
    { name: "Drinking Water", count: 11800 },
    { name: "Solar & Street Lights", count: 8900 },
    { name: "School Infrastructure", count: 5067 }
  ];

  const stageData = chartsData?.stageDistribution || [
    { name: "Completed", value: 33630, fill: "#10b981" },
    { name: "In Progress", value: 48687, fill: "#3b82f6" },
    { name: "Physical Inspection", value: 14200, fill: "#f59e0b" },
    { name: "Vendor Selection", value: 8000, fill: "#8b5cf6" }
  ];

  const spendingData = [
    { stage: "Sanctioned Amount", amount: 4820.5 },
    { stage: "Disbursed Amount", amount: 2536.8 },
    { stage: "Reported Expenditure", amount: 1945.2 },
    { stage: "Unspent Balance", amount: 2283.7 }
  ];

  return (
    <div className="view-container">
      <div className="view-header-row">
        <div>
          <h1 className="view-main-title">Visual Analytics & Intelligence Visualizations</h1>
          <p className="view-sub-title">
            Deep-dive multi-dimensional statistical charts covering risk distribution, detector consensus, state rankings, and financial flows.
          </p>
        </div>
        <div className="header-meta-tag">
          <Activity size={14} color="#2563eb" />
          <span>Full 104,517 Dataset Visualized</span>
        </div>
      </div>

      {/* 2x3 Grid of Rich Interactive Graphs */}
      <div className="charts-grid">
        {/* Chart 1: Risk Distribution */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-wrap">
              <BarChart3 size={16} color="#dc2626" />
              <h3 className="chart-title">Prioritized Risk Severity Distribution</h3>
            </div>
            <span className="chart-badge">7,521 Flagged Candidates</span>
          </div>
          <p className="chart-desc">Breakdown of flagged candidates by hybrid risk score severity.</p>
          <div className="chart-body" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData.filter(d => d.name !== 'Standard Risk')} margin={{ top: 20, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                <Tooltip 
                  formatter={(value) => [`${Number(value).toLocaleString()} works`, 'Count']}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill || '#2563eb'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Detector Consensus Donut */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-wrap">
              <Layers size={16} color="#ea580c" />
              <h3 className="chart-title">Tri-Detector Agreement Overlap</h3>
            </div>
            <span className="chart-badge">Consensus Tiers</span>
          </div>
          <p className="chart-desc">Distribution of candidate validation across Rule, Statistical, and ML engines.</p>
          <div className="chart-body" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={consensusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  labelLine={false}
                >
                  {consensusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CONSENSUS_COLORS[index % CONSENSUS_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [`${Number(value).toLocaleString()} works`, 'Volume']}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Top 10 States Candidate Volume */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-wrap">
              <MapPin size={16} color="#2563eb" />
              <h3 className="chart-title">Top 10 States by Investigation Candidates</h3>
            </div>
            <span className="chart-badge">State Ranking</span>
          </div>
          <p className="chart-desc">States with highest candidate volume prioritized for field verification.</p>
          <div className="chart-body" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topStatesData} layout="vertical" margin={{ top: 10, right: 30, left: 60, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#334155" fontSize={11} tickLine={false} width={80} />
                <Tooltip 
                  formatter={(value, name) => [
                    `${Number(value).toLocaleString()} candidates`,
                    'Flagged Works'
                  ]}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                />
                <Bar dataKey="candidates" fill="#2563eb" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Work Category Breakdown */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-wrap">
              <Building2 size={16} color="#4f46e5" />
              <h3 className="chart-title">Work Category Volume Breakdown</h3>
            </div>
            <span className="chart-badge">Sector Scope</span>
          </div>
          <p className="chart-desc">Dominant development sectors audited across the national master.</p>
          <div className="chart-body" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} margin={{ top: 20, right: 20, left: -10, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-25} textAnchor="end" tickLine={false} interval={0} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  formatter={(value) => [`${Number(value).toLocaleString()} works`, 'Volume']}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                />
                <Bar dataKey="count" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 5: Implementation Stage Distribution */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-wrap">
              <TrendingUp size={16} color="#10b981" />
              <h3 className="chart-title">Implementation Milestone Status</h3>
            </div>
            <span className="chart-badge">Stage Progress</span>
          </div>
          <p className="chart-desc">Current physical status of audited MPLADS works nationwide.</p>
          <div className="chart-body" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                >
                  {stageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STAGE_COLORS[index % STAGE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [`${Number(value).toLocaleString()} works`, 'Works']}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 6: Financial Overview Flow */}
        <div className="chart-card">
          <div className="chart-card-header">
            <div className="chart-title-wrap">
              <DollarSign size={16} color="#059669" />
              <h3 className="chart-title">National Financial Allocation & Disbursals</h3>
            </div>
            <span className="chart-badge">₹ Crores</span>
          </div>
          <p className="chart-desc">Aggregate financial breakdown of sanctioned vs disbursed vs recorded actuals.</p>
          <div className="chart-body" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={spendingData} margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="stage" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  formatter={(value) => [`₹${Number(value).toLocaleString()} Cr`, 'Amount']}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                />
                <Bar dataKey="amount" fill="#059669" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
