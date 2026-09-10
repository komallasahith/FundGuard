import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Brain,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Database,
  FileSearch,
  Filter,
  LayoutDashboard,
  Menu,
  RefreshCw,
  Search,
  ShieldAlert,
  Target,
  X,
  Zap,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const API_BASE = "http://localhost:5000/api";

function App() {
  const [summary, setSummary] = useState(null);
  const [filters, setFilters] = useState({
    mp_names: [],
    work_categories: [],
  });

  const [anomalies, setAnomalies] = useState([]);

  const [selectedWork, setSelectedWork] = useState(null);
  const [selectedExplanation, setSelectedExplanation] = useState(null);

  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("ALL");
  const [mp, setMp] = useState("ALL");
  const [category, setCategory] = useState("ALL");
  const [activeNav, setActiveNav] = useState("dashboard");

  const [sidebarOpen, setSidebarOpen] = useState(false);

  // --------------------------------------------------
  // LOAD DASHBOARD
  // --------------------------------------------------

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [summaryRes, filtersRes, anomaliesRes] = await Promise.all([
        fetch(`${API_BASE}/dashboard/summary`),
        fetch(`${API_BASE}/filters`),
        fetch(`${API_BASE}/anomalies`),
      ]);

      if (!summaryRes.ok) {
        throw new Error("Failed to load dashboard summary");
      }

      if (!filtersRes.ok) {
        throw new Error("Failed to load filters");
      }

      if (!anomaliesRes.ok) {
        throw new Error("Failed to load anomalies");
      }

      const summaryData = await summaryRes.json();
      const filtersData = await filtersRes.json();
      const anomaliesData = await anomaliesRes.json();

      setSummary(summaryData);

      const anomalyArray = Array.isArray(anomaliesData)
        ? anomaliesData
        : Array.isArray(anomaliesData?.anomalies)
        ? anomaliesData.anomalies
        : Array.isArray(anomaliesData?.data)
        ? anomaliesData.data
        : Array.isArray(anomaliesData?.results)
        ? anomaliesData.results
        : [];

      const uniqueMps = Array.from(
        new Set(
          anomalyArray
            .map(
              (item) =>
                item?.mp_name ||
                item?.MP_NAME ||
                item?.identity?.mp_name
            )
            .filter(Boolean)
        )
      ).sort();

      const uniqueCategories = Array.from(
        new Set(
          anomalyArray
            .map(
              (item) =>
                item?.work_category ||
                item?.WORK_CATEGORY ||
                item?.identity?.work_category
            )
            .filter(Boolean)
        )
      ).sort();

      const riskLevels = Array.isArray(filtersData?.risk_levels)
        ? filtersData.risk_levels
        : ["HIGH", "MEDIUM", "LOW"];

      setFilters({
        mp_names: Array.isArray(filtersData?.mp_names)
          ? filtersData.mp_names
          : uniqueMps,
        work_categories: Array.isArray(filtersData?.work_categories)
          ? filtersData.work_categories
          : uniqueCategories,
        risk_levels: riskLevels,
      });

      setAnomalies(anomalyArray);
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to load dashboard");
      setAnomalies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // --------------------------------------------------
  // LOAD WORK DETAIL
  // --------------------------------------------------

  const openWork = async (workId) => {
    try {
      setDetailLoading(true);
      setSelectedWork(null);
      setSelectedExplanation(null);

      const detailRes = await fetch(
        `${API_BASE}/anomalies/${encodeURIComponent(workId)}`
      );

      if (!detailRes.ok) {
        throw new Error("Failed to load work details");
      }

      const detailData = await detailRes.json();

      setSelectedWork(detailData);

      // Explanation can either be inside the detail response
      // or loaded from the separate endpoint.
      if (detailData?.ai_explanation) {
        setSelectedExplanation(detailData.ai_explanation);
      } else {
        try {
          const explanationRes = await fetch(
            `${API_BASE}/anomalies/${encodeURIComponent(workId)}/explanation`
          );

          if (explanationRes.ok) {
            const explanationData = await explanationRes.json();
            setSelectedExplanation(
              explanationData?.explanation || explanationData
            );
          }
        } catch (explanationError) {
          console.warn(
            "AI explanation could not be loaded:",
            explanationError
          );
        }
      }
    } catch (err) {
      console.error(err);
      alert(err.message || "Unable to load work details");
    } finally {
      setDetailLoading(false);
    }
  };

  // --------------------------------------------------
  // FILTERING
  // --------------------------------------------------

  const filteredAnomalies = useMemo(() => {
    const works = Array.isArray(anomalies) ? anomalies : [];

    return works.filter((work) => {
      const workId = String(
        work?.work_id ??
          work?.WORK_RECOMMENDATION_DTL_ID ??
          work?.WORK_ID ??
          ""
      );

      const mpName = String(
        work?.mp_name ??
          work?.MP_NAME ??
          work?.identity?.mp_name ??
          ""
      );

      const workCategory = String(
        work?.work_category ??
          work?.WORK_CATEGORY ??
          work?.identity?.work_category ??
          ""
      );

      const riskLevel = String(
        work?.risk_level ??
          work?.FINAL_RISK_LEVEL ??
          work?.risk?.risk_level ??
          ""
      ).toUpperCase();

      const searchText = search.toLowerCase().trim();

      const matchesSearch =
        !searchText ||
        workId.toLowerCase().includes(searchText) ||
        mpName.toLowerCase().includes(searchText);

      const matchesRisk =
        risk === "ALL" || riskLevel === risk.toUpperCase();

      const matchesMp =
        mp === "ALL" || mpName === mp;

      const matchesCategory =
        category === "ALL" || workCategory === category;

      return (
        matchesSearch &&
        matchesRisk &&
        matchesMp &&
        matchesCategory
      );
    });
  }, [anomalies, search, risk, mp, category]);

  // --------------------------------------------------
  // CHART DATA
  // --------------------------------------------------

  const riskChartData = [
    {
      name: "High",
      value: Number(summary?.risk_distribution?.high || 0),
    },
    {
      name: "Medium",
      value: Number(summary?.risk_distribution?.medium || 0),
    },
    {
      name: "Low",
      value: Number(summary?.risk_distribution?.low || 0),
    },
  ];

  const agreementChartData = [
    {
      name: "Strong",
      value: Number(summary?.detector_agreement?.strong || 0),
    },
    {
      name: "Moderate",
      value: Number(summary?.detector_agreement?.moderate || 0),
    },
    {
      name: "Single Detector",
      value: Number(summary?.detector_agreement?.single_detector || 0),
    },
  ];

  // --------------------------------------------------
  // HELPERS
  // --------------------------------------------------

  const formatNumber = (value) => {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "—";
    }

    return number.toLocaleString("en-IN");
  };

  const formatAmount = (value) => {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "—";
    }

    return `₹${number.toLocaleString("en-IN", {
      maximumFractionDigits: 0,
    })}`;
  };

  const formatScore = (value) => {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return "—";
    }

    return number.toFixed(2);
  };

  const getRiskClass = (level) => {
    const value = String(level || "").toUpperCase();

    if (value === "HIGH" || value === "CRITICAL") {
      return "risk-high";
    }

    if (value === "MEDIUM") {
      return "risk-medium";
    }

    return "risk-low";
  };

  const getRiskIcon = (level) => {
    const value = String(level || "").toUpperCase();

    if (value === "HIGH" || value === "CRITICAL") {
      return <CircleAlert size={15} />;
    }

    if (value === "MEDIUM") {
      return <AlertTriangle size={15} />;
    }

    return <CheckCircle2 size={15} />;
  };

  const getWorkId = (work) => {
    return (
      work?.work_id ??
      work?.WORK_RECOMMENDATION_DTL_ID ??
      work?.WORK_ID ??
      "—"
    );
  };

  const getMpName = (work) => {
    return (
      work?.mp_name ??
      work?.MP_NAME ??
      work?.identity?.mp_name ??
      "Unknown MP"
    );
  };

  const getCategory = (work) => {
    return (
      work?.work_category ??
      work?.WORK_CATEGORY ??
      work?.identity?.work_category ??
      "Unknown"
    );
  };

  const getActivity = (work) => {
    return (
      work?.activity_name ??
      work?.ACTIVITY_NAME ??
      work?.identity?.activity_name ??
      "—"
    );
  };

  const getRiskLevel = (work) => {
    return (
      work?.risk_level ??
      work?.FINAL_RISK_LEVEL ??
      work?.risk?.risk_level ??
      "LOW"
    );
  };

  const getHybridScore = (work) => {
    return (
      work?.hybrid_risk_score ??
      work?.HYBRID_RISK_SCORE ??
      work?.risk?.hybrid_score ??
      null
    );
  };

  const getAgreement = (work) => {
    return (
      work?.detector_agreement ??
      work?.DETECTOR_AGREEMENT ??
      work?.risk?.detector_agreement ??
      "NONE"
    );
  };

  // --------------------------------------------------
  // EVIDENCE RENDERER
  // --------------------------------------------------

  const renderEvidence = (evidence) => {
    if (!evidence || typeof evidence !== "object") {
      return (
        <div className="empty-evidence">
          No structured evidence available.
        </div>
      );
    }

    const groups = [
      {
        key: "financial",
        title: "Financial Evidence",
      },
      {
        key: "statistical",
        title: "Statistical Evidence",
      },
      {
        key: "transaction",
        title: "Transaction Evidence",
      },
      {
        key: "timeline",
        title: "Timeline Evidence",
      },
    ];

    return (
      <div className="evidence-list">
        {groups.map((group) => {
          const items = Array.isArray(evidence[group.key])
            ? evidence[group.key]
            : [];

          if (items.length === 0) {
            return null;
          }

          return (
            <div className="evidence-group" key={group.key}>
              <div className="evidence-group-title">
                {group.title}
              </div>

              {items.map((item, index) => (
                <div
                  className="evidence-item"
                  key={`${group.key}-${index}`}
                >
                  <div className="evidence-item-header">
                    <span className="evidence-type">
                      {String(item?.type || "finding")
                        .replaceAll("_", " ")
                        .toUpperCase()}
                    </span>

                    {item?.severity && (
                      <span
                        className={`severity ${String(
                          item.severity
                        ).toLowerCase()}`}
                      >
                        {item.severity}
                      </span>
                    )}
                  </div>

                  <div className="evidence-finding">
                    {item?.finding || "Evidence detected."}
                  </div>

                  {item?.ratio !== undefined &&
                    item?.ratio !== null && (
                      <div className="evidence-meta">
                        Ratio: {formatScore(item.ratio)}×
                      </div>
                    )}

                  {item?.days !== undefined &&
                    item?.days !== null && (
                      <div className="evidence-meta">
                        Days: {formatNumber(item.days)}
                      </div>
                    )}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    );
  };

  // --------------------------------------------------
  // LOADING
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-logo">
            <ShieldAlert size={30} />
          </div>

          <h2>FundGuard AI</h2>

          <p>Loading anomaly intelligence...</p>

          <div className="loading-spinner">
            <RefreshCw size={22} />
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------
  // ERROR
  // --------------------------------------------------

  if (error) {
    return (
      <div className="error-screen">
        <div className="error-card">
          <CircleAlert size={42} />

          <h2>Unable to load FundGuard AI</h2>

          <p>{error}</p>

          <div className="error-help">
            Make sure the Node.js backend is running on:
            <strong> http://localhost:5000</strong>
          </div>

          <button className="primary-button" onClick={loadDashboard}>
            <RefreshCw size={17} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  // --------------------------------------------------
  // MAIN APP
  // --------------------------------------------------

  return (
    <div className="app-shell">
      {/* SIDEBAR OVERLAY MOBILE */}

      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* SIDEBAR */}

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-icon">
            <ShieldAlert size={25} />
          </div>

          <div>
            <div className="brand-name">FundGuard</div>
            <div className="brand-ai">AI</div>
          </div>

          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">MONITORING</div>

          <button
            className={`nav-item ${activeNav === "dashboard" ? "active" : ""}`}
            onClick={() => {
              setActiveNav("dashboard");
              setSidebarOpen(false);
            }}
          >
            <LayoutDashboard size={18} />
            Dashboard
          </button>

          <button
            className={`nav-item ${activeNav === "anomalies" ? "active" : ""}`}
            onClick={() => {
              setActiveNav("anomalies");
              setSidebarOpen(false);
            }}
          >
            <AlertTriangle size={18} />
            Anomalies
          </button>

          <button
            className={`nav-item ${activeNav === "investigations" ? "active" : ""}`}
            onClick={() => {
              setActiveNav("investigations");
              setSidebarOpen(false);
            }}
          >
            <FileSearch size={18} />
            Investigations
          </button>

          <div className="nav-section-title second">
            INTELLIGENCE
          </div>

          <button
            className={`nav-item ${activeNav === "ai" ? "active" : ""}`}
            onClick={() => {
              setActiveNav("ai");
              setSidebarOpen(false);
            }}
          >
            <Brain size={18} />
            AI Reasoning
          </button>

          <button
            className={`nav-item ${activeNav === "analytics" ? "active" : ""}`}
            onClick={() => {
              setActiveNav("analytics");
              setSidebarOpen(false);
            }}
          >
            <BarChart3 size={18} />
            Analytics
          </button>

          <button
            className={`nav-item ${activeNav === "data" ? "active" : ""}`}
            onClick={() => {
              setActiveNav("data");
              setSidebarOpen(false);
            }}
          >
            <Database size={18} />
            Data Sources
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <div className="status-dot" />
            <div>
              <div className="status-title">System Online</div>
              <div className="status-text">
                Analytics engine active
              </div>
            </div>
          </div>

          <div className="sidebar-version">
            FundGuard AI · SIH 2026
          </div>
        </div>
      </aside>

      {/* MAIN */}

      <main className="main-content">
        {/* MOBILE TOPBAR */}

        <div className="mobile-topbar">
          <button
            className="menu-button"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={22} />
          </button>

          <div className="mobile-brand">
            <ShieldAlert size={20} />
            FundGuard AI
          </div>
        </div>

        {/* HEADER */}

        <header className="page-header">
          <div>
            <div className="breadcrumb">
              <span>FundGuard AI</span>
              <ChevronRight size={13} />
              <span>Command Center</span>
            </div>

            <h1>Fund Monitoring Command Center</h1>

            <p>
              AI-powered anomaly detection for MPLADS implementation
            </p>
          </div>

          <button className="refresh-button" onClick={loadDashboard}>
            <RefreshCw size={16} />
            Refresh Data
          </button>
        </header>

        {/* HERO */}

        <section className="hero-card">
          <div className="hero-left">
            <div className="hero-icon">
              <Zap size={25} />
            </div>

            <div>
              <div className="hero-label">
                AI RISK INTELLIGENCE
              </div>

              <h2>
                Detect unusual spending before it becomes a problem.
              </h2>

              <p>
                FundGuard combines deterministic rules, statistical
                analysis and machine learning to identify works that
                deserve human investigation.
              </p>
            </div>
          </div>

          <div className="hero-badge">
            <Activity size={16} />
            LIVE ANALYTICS
          </div>
        </section>

        {/* STATS */}

        <section className="stats-grid">
          <StatCard
            icon={<Database size={20} />}
            label="Works Analyzed"
            value={formatNumber(summary?.total_works_analyzed)}
            description="Unique analytical works"
          />

          <StatCard
            icon={<ShieldAlert size={20} />}
            label="High Risk"
            value={formatNumber(
              summary?.risk_distribution?.high
            )}
            description="Priority investigation track"
            accent="high"
          />

          <StatCard
            icon={<AlertTriangle size={20} />}
            label="Medium Risk"
            value={formatNumber(
              summary?.risk_distribution?.medium
            )}
            description="Requires human review"
            accent="medium"
          />

          <StatCard
            icon={<Target size={20} />}
            label="Strong Detector Agreement"
            value={formatNumber(
              summary?.detector_agreement?.strong
            )}
            description="3 detector signals agree"
          />
        </section>

        {/* CHARTS */}

        <section className="charts-grid">
          <div className="panel chart-panel">
            <div className="panel-header">
              <div>
                <h3>Risk Distribution</h3>
                <p>Current analytical risk classification</p>
              </div>

              <BarChart3 size={20} />
            </div>

            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskChartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 12 }}
                  />

                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 12 }}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="value"
                    radius={[6, 6, 0, 0]}
                  >
                    {riskChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel chart-panel">
            <div className="panel-header">
              <div>
                <h3>Detector Agreement</h3>
                <p>How many detection engines agree</p>
              </div>

              <Brain size={20} />
            </div>

            <div className="chart-container pie-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={agreementChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={95}
                    innerRadius={55}
                    paddingAngle={3}
                  >
                    {agreementChartData.map((entry, index) => (
                      <Cell key={`pie-${index}`} />
                    ))}
                  </Pie>

                  <Tooltip />

                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* FILTER PANEL */}

        <section className="panel filter-panel">
          <div className="filter-header">
            <div>
              <h3>
                <Filter size={18} />
                Investigation Queue
              </h3>

              <p>
                {formatNumber(filteredAnomalies.length)} works
                matching current filters
              </p>
            </div>

            {(search ||
              risk !== "ALL" ||
              mp !== "ALL" ||
              category !== "ALL") && (
              <button
                className="clear-button"
                onClick={() => {
                  setSearch("");
                  setRisk("ALL");
                  setMp("ALL");
                  setCategory("ALL");
                }}
              >
                Clear filters
              </button>
            )}
          </div>

          <div className="filters">
            {/* SEARCH */}

            <div className="search-box">
              <Search size={17} />

              <input
                type="text"
                placeholder="Search work ID or MP..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            {/* RISK */}

            <select
              value={risk}
              onChange={(e) => setRisk(e.target.value)}
            >
              <option value="ALL">All Risk Levels</option>

              {(Array.isArray(filters?.risk_levels)
                ? filters.risk_levels
                : ["HIGH", "MEDIUM", "LOW"]
              ).map((level) => (
                <option key={level} value={level}>
                  {String(level)
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (ch) => ch.toUpperCase())}
                </option>
              ))}
            </select>

            {/* MP */}

            <select
              value={mp}
              onChange={(e) => setMp(e.target.value)}
            >
              <option value="ALL">All MPs</option>

              {(Array.isArray(filters?.mp_names)
                ? filters.mp_names
                : []
              ).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>

            {/* CATEGORY */}

            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="ALL">All Categories</option>

              {(Array.isArray(filters?.work_categories)
                ? filters.work_categories
                : []
              ).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        </section>

        {/* ANOMALY TABLE */}

        <section className="panel table-panel">
          <div className="panel-header table-title">
            <div>
              <h3>Detected Works</h3>
              <p>
                Ranked using hybrid rule, statistical and ML signals
              </p>
            </div>

            <div className="record-count">
              {filteredAnomalies.length} records
            </div>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>PRIORITY</th>
                  <th>WORK ID</th>
                  <th>MP / CONSTITUENCY</th>
                  <th>WORK</th>
                  <th>RISK</th>
                  <th>HYBRID SCORE</th>
                  <th>DETECTOR AGREEMENT</th>
                  <th>ACTION</th>
                </tr>
              </thead>

              <tbody>
                {filteredAnomalies.length === 0 ? (
                  <tr>
                    <td colSpan="8">
                      <div className="empty-state">
                        <Search size={30} />
                        <strong>No matching works</strong>
                        <span>
                          Try changing the current filters.
                        </span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredAnomalies.map((work) => {
                    const workId = getWorkId(work);
                    const riskLevel = getRiskLevel(work);
                    const score = getHybridScore(work);
                    const agreement = getAgreement(work);
                    const priority = Number(
                      work?.investigation_priority ??
                        work?.priority ??
                        work?.risk?.investigation_priority ??
                        4
                    );

                    return (
                      <tr key={workId}>
                        <td>
                          <span className={`priority-badge priority-${priority}`}>
                            P{priority}
                          </span>
                        </td>

                        <td>
                          <span className="work-id">
                            {workId}
                          </span>
                        </td>

                        <td>
                          <div className="mp-cell">
                            <strong>{getMpName(work)}</strong>

                            <span>
                              {work?.constituency ??
                                work?.CONSTITUENCY_NAME ??
                                work?.identity?.constituency ??
                                "Unknown constituency"}
                            </span>
                          </div>
                        </td>

                        <td>
                          <div className="work-cell">
                            <strong>{getCategory(work)}</strong>

                            <span title={getActivity(work)}>
                              {getActivity(work)}
                            </span>
                          </div>
                        </td>

                        <td>
                          <span
                            className={`risk-badge ${getRiskClass(
                              riskLevel
                            )}`}
                          >
                            {getRiskIcon(riskLevel)}
                            {String(riskLevel).toUpperCase()}
                          </span>
                        </td>

                        <td>
                          <span className="score-value">
                            {formatScore(score)}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`agreement-badge ${String(
                              agreement
                            )
                              .toLowerCase()
                              .replaceAll(" ", "-")}`}
                          >
                            {agreement}
                          </span>
                        </td>

                        <td>
                          <button
                            className="view-button"
                            onClick={() => openWork(workId)}
                          >
                            Investigate
                            <ChevronRight size={15} />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* FOOTER */}

        <footer className="page-footer">
          <div>
            FundGuard AI identifies anomaly/risk candidates for
            investigation.
          </div>

          <div>
            It does <strong>not</strong> establish fraud or
            wrongdoing.
          </div>
        </footer>
      </main>

      {/* DETAIL DRAWER */}

      {(selectedWork || detailLoading) && (
        <div
          className="drawer-overlay"
          onClick={() => {
            if (!detailLoading) {
              setSelectedWork(null);
              setSelectedExplanation(null);
            }
          }}
        >
          <aside
            className="detail-drawer"
            onClick={(e) => e.stopPropagation()}
          >
            {/* DRAWER HEADER */}

            <div className="drawer-header">
              <div>
                <div className="drawer-kicker">
                  INVESTIGATION DETAIL
                </div>

                <h2>
                  Work #
                  {selectedWork
                    ? getWorkId(
                        selectedWork?.risk ||
                          selectedWork?.evidence ||
                          selectedWork
                      )
                    : "—"}
                </h2>
              </div>

              <button
                className="drawer-close"
                onClick={() => {
                  setSelectedWork(null);
                  setSelectedExplanation(null);
                }}
              >
                <X size={21} />
              </button>
            </div>

            {detailLoading ? (
              <div className="drawer-loading">
                <RefreshCw size={25} />
                <span>Loading investigation...</span>
              </div>
            ) : (
              <div className="drawer-body">
                <DetailContent
                  work={selectedWork}
                  explanation={selectedExplanation}
                  formatAmount={formatAmount}
                  formatNumber={formatNumber}
                  formatScore={formatScore}
                  getRiskClass={getRiskClass}
                  renderEvidence={renderEvidence}
                />
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

// ======================================================
// STAT CARD
// ======================================================

function StatCard({
  icon,
  label,
  value,
  description,
  accent,
}) {
  return (
    <div className={`stat-card ${accent || ""}`}>
      <div className="stat-icon">{icon}</div>

      <div className="stat-content">
        <div className="stat-label">{label}</div>

        <div className="stat-value">{value}</div>

        <div className="stat-description">
          {description}
        </div>
      </div>
    </div>
  );
}

// ======================================================
// DETAIL CONTENT
// ======================================================

function DetailContent({
  work,
  explanation,
  formatAmount,
  formatNumber,
  formatScore,
  getRiskClass,
  renderEvidence,
}) {
  if (!work) {
    return null;
  }

  /*
   * Backend detail response is expected to contain:
   *
   * {
   *   work_id,
   *   identity,
   *   risk,
   *   detector_scores,
   *   financial,
   *   statistical,
   *   transactions,
   *   timeline,
   *   evidence,
   *   summary,
   *   investigation_guidance,
   *   disclaimer
   * }
   */

  const identity = work?.identity || {};
  const risk = work?.risk || {};
  const detectorScores = work?.detector_scores || {};
  const financial = work?.financial || {};
  const statistical = work?.statistical || {};
  const transactions = work?.transactions || {};
  const timeline = work?.timeline || {};
  const evidence = work?.evidence || {};

  const ai =
    explanation?.explanation ||
    explanation?.ai_explanation ||
    explanation ||
    null;

  const getAiField = (field) => {
    if (!ai || typeof ai !== "object") {
      return null;
    }

    return (
      ai[field] ??
      ai[`ai_${field}`] ??
      null
    );
  };

  const whyFlagged =
    getAiField("why_flagged") ||
    getAiField("reason") ||
    null;

  const keyEvidence =
    getAiField("key_evidence") ||
    getAiField("evidence") ||
    [];

  const investigationChecks =
    getAiField("investigation_checks") ||
    getAiField("recommended_checks") ||
    [];

  const assessment =
    getAiField("assessment") ||
    getAiField("risk_assessment") ||
    null;

  const limitations =
    getAiField("limitations") ||
    [];

  return (
    <>
      {/* RISK SUMMARY */}

      <div className="detail-risk-card">
        <div>
          <div className="detail-risk-label">
            HYBRID RISK SCORE
          </div>

          <div className="detail-risk-score">
            {formatScore(risk?.hybrid_score)}
          </div>
        </div>

        <div className="detail-risk-right">
          <span
            className={`risk-badge ${getRiskClass(
              risk?.risk_level
            )}`}
          >
            {risk?.risk_level || "LOW"}
          </span>

          <span className="agreement-text">
            {risk?.detector_agreement || "NONE"}
            {risk?.detector_agreement_count
              ? ` · ${risk.detector_agreement_count}/3 detectors`
              : ""}
          </span>
        </div>
      </div>

      {/* IDENTITY */}

      <DetailSection title="Work Identity">
        <div className="detail-grid">
          <DetailField
            label="MP"
            value={identity?.mp_name}
          />

          <DetailField
            label="Constituency"
            value={identity?.constituency}
          />

          <DetailField
            label="Category"
            value={identity?.work_category}
          />

          <DetailField
            label="Work ID"
            value={work?.work_id}
          />

          <div className="detail-field full">
            <span>Activity</span>
            <strong>
              {identity?.activity_name || "—"}
            </strong>
          </div>
        </div>
      </DetailSection>

      {/* DETECTORS */}

      <DetailSection title="Detector Signals">
        <div className="detector-grid">
          <DetectorCard
            title="Rule Engine"
            value={detectorScores?.rule}
            description="Deterministic rules"
          />

          <DetectorCard
            title="Statistics"
            value={detectorScores?.statistical}
            description="Peer-based statistical signal"
          />

          <DetectorCard
            title="Isolation Forest"
            value={detectorScores?.isolation_forest}
            description="Unsupervised ML signal"
          />
        </div>
      </DetailSection>

      {/* FINANCIAL */}

      <DetailSection title="Financial Evidence">
        <div className="detail-grid">
          <DetailField
            label="Recommended"
            value={formatAmount(
              financial?.recommended_amount
            )}
          />

          <DetailField
            label="Sanctioned"
            value={formatAmount(
              financial?.sanction_amount
            )}
          />

          <DetailField
            label="Actual Amount"
            value={formatAmount(
              financial?.actual_amount
            )}
          />

          <DetailField
            label="Disbursed"
            value={formatAmount(
              financial?.disbursed_amount
            )}
          />

          <DetailField
            label="Peer Cost Ratio"
            value={
              financial?.cost_vs_peer_median !== null &&
              financial?.cost_vs_peer_median !== undefined
                ? `${formatScore(
                    financial.cost_vs_peer_median
                  )}×`
                : "—"
            }
          />

          <DetailField
            label="Peer Z-Score"
            value={formatScore(
              statistical?.peer_z_score
            )}
          />
        </div>
      </DetailSection>

      {/* TRANSACTIONS */}

      <DetailSection title="Transaction Profile">
        <div className="detail-grid">
          <DetailField
            label="Transactions"
            value={formatNumber(
              transactions?.transaction_count
            )}
          />

          <DetailField
            label="Vendors"
            value={formatNumber(
              transactions?.vendor_count
            )}
          />

          <DetailField
            label="Max Transaction"
            value={formatAmount(
              transactions?.max_transaction_amount
            )}
          />
        </div>
      </DetailSection>

      {/* TIMELINE */}

      <DetailSection title="Implementation Timeline">
        <div className="timeline">
          <TimelineItem
            title="Recommendation"
            date={timeline?.recommendation_date}
          />

          <TimelineItem
            title="Sanction"
            date={timeline?.sanction_date}
            days={timeline?.days_recommendation_to_sanction}
          />

          <TimelineItem
            title="Completion"
            date={timeline?.completion_date}
            days={timeline?.days_sanction_to_completion}
          />
        </div>
      </DetailSection>

      {/* STRUCTURED EVIDENCE */}

      <DetailSection title="Structured Evidence">
        {renderEvidence(evidence)}
      </DetailSection>

      {/* SUMMARY */}

      {work?.summary && (
        <DetailSection title="System Summary">
          <div className="summary-box">
            {work.summary}
          </div>
        </DetailSection>
      )}

      {/* AI EXPLANATION */}

      {ai && (
        <div className="ai-section">
          <div className="ai-section-header">
            <div className="ai-icon">
              <Brain size={19} />
            </div>

            <div>
              <h3>AI Investigation Reasoning</h3>
              <p>
                Explanation generated from structured evidence
              </p>
            </div>
          </div>

          {whyFlagged && (
            <div className="ai-block">
              <div className="ai-block-title">
                Why was this flagged?
              </div>

              <div className="ai-text">
                {whyFlagged}
              </div>
            </div>
          )}

          {Array.isArray(keyEvidence) &&
            keyEvidence.length > 0 && (
              <div className="ai-block">
                <div className="ai-block-title">
                  Key Evidence
                </div>

                <ul className="ai-list">
                  {keyEvidence.map((item, index) => (
                    <li key={index}>
                      {typeof item === "string"
                        ? item
                        : item?.finding ||
                          item?.description ||
                          JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              </div>
            )}

          {Array.isArray(investigationChecks) &&
            investigationChecks.length > 0 && (
              <div className="ai-block">
                <div className="ai-block-title">
                  Investigation Checks
                </div>

                <ul className="ai-list">
                  {investigationChecks.map((item, index) => (
                    <li key={index}>
                      {typeof item === "string"
                        ? item
                        : item?.check ||
                          item?.action ||
                          item?.description ||
                          JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              </div>
            )}

          {assessment && (
            <div className="ai-block">
              <div className="ai-block-title">
                Assessment
              </div>

              <div className="ai-text">
                {assessment}
              </div>
            </div>
          )}

          {Array.isArray(limitations) &&
            limitations.length > 0 && (
              <div className="ai-block limitations">
                <div className="ai-block-title">
                  Limitations
                </div>

                <ul className="ai-list">
                  {limitations.map((item, index) => (
                    <li key={index}>
                      {typeof item === "string"
                        ? item
                        : item?.description ||
                          JSON.stringify(item)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      )}

      {/* INVESTIGATION GUIDANCE */}

      {work?.investigation_guidance && (
        <DetailSection title="Investigation Guidance">
          <div className="guidance-box">
            <FileSearch size={18} />

            <span>
              {work.investigation_guidance}
            </span>
          </div>
        </DetailSection>
      )}

      {/* DISCLAIMER */}

      <div className="detail-disclaimer">
        <AlertTriangle size={17} />

        <span>
          {work?.disclaimer ||
            "FundGuard identifies anomaly/risk candidates for investigation. It does not establish fraud or wrongdoing."}
        </span>
      </div>
    </>
  );
}

// ======================================================
// DETAIL SECTION
// ======================================================

function DetailSection({ title, children }) {
  return (
    <section className="detail-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

// ======================================================
// DETAIL FIELD
// ======================================================

function DetailField({ label, value }) {
  return (
    <div className="detail-field">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
    </div>
  );
}

// ======================================================
// DETECTOR CARD
// ======================================================

function DetectorCard({
  title,
  value,
  description,
}) {
  const number = Number(value);

  return (
    <div className="detector-card">
      <div className="detector-title">
        {title}
      </div>

      <div className="detector-score">
        {Number.isFinite(number)
          ? number.toFixed(1)
          : "—"}
      </div>

      <div className="detector-description">
        {description}
      </div>
    </div>
  );
}

// ======================================================
// TIMELINE ITEM
// ======================================================

function TimelineItem({
  title,
  date,
  days,
}) {
  return (
    <div className="timeline-item">
      <div className="timeline-dot" />

      <div className="timeline-content">
        <strong>{title}</strong>

        <span>{date || "Not available"}</span>

        {days !== null &&
          days !== undefined &&
          Number.isFinite(Number(days)) && (
            <small>
              {Number(days).toLocaleString("en-IN")} days
            </small>
          )}
      </div>
    </div>
  );
}

export default App;