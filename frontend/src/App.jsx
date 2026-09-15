import { useState, useEffect, useCallback, useRef } from 'react';
import Navbar from './components/Navbar.jsx';
import OverviewView from './components/OverviewView.jsx';
import AnalyticsChartsView from './components/AnalyticsChartsView.jsx';
import IndiaMapView from './components/IndiaMapView.jsx';
import WorksExplorerView from './components/WorksExplorerView.jsx';
import DetectorEngineView from './components/DetectorEngineView.jsx';
import PaymentIntelligenceView from './components/PaymentIntelligenceView.jsx';
import InvestigationDrawer from './components/InvestigationDrawer.jsx';

import { 
  fetchSummary, 
  fetchFilters, 
  fetchAnomalies, 
  fetchAnomaly, 
  fetchExplanation,
  generateExplanation,
  fetchHealth,
  fetchOverview,
  fetchStates,
  triggerReload
} from './services/api.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'analytics' | 'map' | 'explorer' | 'detectors' | 'payments'
  const [scope, setScope] = useState('candidates'); // 'candidates' | 'all'

  const [summary, setSummary] = useState(null);
  const [overview, setOverview] = useState(null);
  const [statesData, setStatesData] = useState([]);
  const [health, setHealth] = useState(null);
  const [filters, setFilters] = useState({ 
    states: [], 
    constituencies: [], 
    mps: [], 
    risk_levels: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], 
    priorities: ['P1', 'P2', 'P3', 'P4'],
    detector_agreements: [] 
  });
  const [anomalies, setAnomalies] = useState([]);
  const [pagination, setPagination] = useState({ total: 7521, limit: 50, offset: 0 });

  // Filters state
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('ALL');
  const [constituencyFilter, setConstituencyFilter] = useState('ALL');
  const [mpFilter, setMpFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [agreementFilter, setAgreementFilter] = useState('ALL');

  // Selected work for Investigation Drawer
  const [selectedWork, setSelectedWork] = useState(null);
  const [selectedExplanation, setSelectedExplanation] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [generatingAI, setGeneratingAI] = useState(false);

  const [loading, setLoading] = useState(true);
  const [reloading, setReloading] = useState(false);
  const isFirstRender = useRef(true);

  // Load filter metadata
  const loadFilterOptions = useCallback(async (stateVal) => {
    try {
      const filtersRes = await fetchFilters(stateVal && stateVal !== 'ALL' ? { state: stateVal } : {});
      if (filtersRes) {
        setFilters(prev => ({
          ...prev,
          states: filtersRes.states || prev.states,
          constituencies: filtersRes.constituencies || [],
          mps: filtersRes.mps || [],
          risk_levels: filtersRes.risk_levels || ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
          priorities: filtersRes.priorities || ['P1', 'P2', 'P3', 'P4'],
          detector_agreements: filtersRes.detector_agreements || prev.detector_agreements
        }));
      }
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  }, []);

  // Fetch Dashboard dataset
  const loadDashboardData = useCallback(async (
    currentOffset = 0,
    currScope = scope,
    currState = stateFilter,
    currConstituency = constituencyFilter,
    currMp = mpFilter,
    currRisk = riskFilter,
    currPriority = priorityFilter,
    currAgreement = agreementFilter,
    currSearch = search
  ) => {
    try {
      setLoading(true);
      const [summaryRes, anomaliesRes, healthRes, overviewRes, statesRes] = await Promise.all([
        fetchSummary({
          state: currState,
          constituency: currConstituency,
          mp: currMp,
          risk: currRisk,
          priority: currPriority,
          agreement: currAgreement
        }).catch(() => null),
        fetchAnomalies({
          state: currState,
          constituency: currConstituency,
          mp: currMp,
          risk: currRisk,
          priority: currPriority,
          agreement: currAgreement,
          search: currSearch,
          scope: currScope,
          limit: 50,
          offset: currentOffset
        }).catch(() => null),
        fetchHealth().catch(() => null),
        fetchOverview().catch(() => null),
        fetchStates().catch(() => null)
      ]);

      if (overviewRes?.overview) setOverview(overviewRes.overview);
      if (Array.isArray(statesRes?.states)) setStatesData(statesRes.states);
      if (healthRes) setHealth(healthRes);
      if (summaryRes) setSummary(summaryRes);
      if (anomaliesRes) {
        setAnomalies(Array.isArray(anomaliesRes.results) ? anomaliesRes.results : []);
        setPagination({
          total: Number(anomaliesRes.total) || 0,
          limit: Number(anomaliesRes.limit) || 50,
          offset: Number(anomaliesRes.offset) || 0
        });
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [scope, stateFilter, constituencyFilter, mpFilter, riskFilter, priorityFilter, agreementFilter, search]);

  useEffect(() => {
    loadFilterOptions();
    loadDashboardData(0);
  }, [loadFilterOptions, loadDashboardData]);

  useEffect(() => {
    loadFilterOptions(stateFilter);
  }, [stateFilter, loadFilterOptions]);

  // Debounced filter effect
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const timer = setTimeout(() => {
      loadDashboardData(0, scope, stateFilter, constituencyFilter, mpFilter, riskFilter, priorityFilter, agreementFilter, search);
    }, 250);

    return () => clearTimeout(timer);
  }, [scope, stateFilter, constituencyFilter, mpFilter, riskFilter, priorityFilter, agreementFilter, search, loadDashboardData]);

  const handlePageChange = async (newOffset) => {
    try {
      setLoading(true);
      const aData = await fetchAnomalies({
        state: stateFilter,
        constituency: constituencyFilter,
        mp: mpFilter,
        risk: riskFilter,
        priority: priorityFilter,
        agreement: agreementFilter,
        search,
        scope,
        limit: 50,
        offset: newOffset
      });

      setAnomalies(aData.results || []);
      setPagination({
        total: aData.total || 0,
        limit: aData.limit || 50,
        offset: aData.offset || 0
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Pagination fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilters = () => {
    setSearch('');
    setStateFilter('ALL');
    setConstituencyFilter('ALL');
    setMpFilter('ALL');
    setRiskFilter('ALL');
    setPriorityFilter('ALL');
    setAgreementFilter('ALL');
  };

  const handleOpenWork = async (workId) => {
    if (!workId) return;
    try {
      setDrawerOpen(true);
      setDrawerLoading(true);
      setSelectedWork(null);
      setSelectedExplanation(null);

      const anomalyDetail = await fetchAnomaly(workId);
      let aiExplanation = anomalyDetail?.ai_explanation || null;

      if (!aiExplanation && anomalyDetail?.ai_available) {
        try {
          const expRes = await fetchExplanation(workId);
          aiExplanation = expRes?.explanation || expRes;
        } catch {
          // fallback
        }
      }

      setSelectedWork(anomalyDetail);
      setSelectedExplanation(aiExplanation);
    } catch (err) {
      console.error('Failed to open work dossier:', err);
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleGenerateAI = async (workId) => {
    if (!workId) return;
    try {
      setGeneratingAI(true);
      const expRes = await generateExplanation(workId);
      if (expRes && expRes.explanation) {
        setSelectedExplanation(expRes.explanation);
      }
    } catch (err) {
      console.error('Failed to generate AI explanation:', err);
    } finally {
      setGeneratingAI(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setReloading(true);
      await triggerReload();
      await loadDashboardData(0);
    } catch (err) {
      console.error('Reload failed:', err);
    } finally {
      setReloading(false);
    }
  };

  return (
    <div className="fundguard-app">
      {/* Top GovTech Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        summary={summary}
        health={health}
        overview={overview}
        onRefresh={handleRefresh}
        reloading={reloading}
      />

      {/* Main Tab Content */}
      <main className="fundguard-main">
        {activeTab === 'overview' && (
          <OverviewView
            overview={overview}
            summary={summary}
            onSelectRisk={(riskTier) => setRiskFilter(riskTier)}
            onNavigateToTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsChartsView />
        )}

        {activeTab === 'map' && (
          <IndiaMapView
            statesData={statesData}
            selectedState={stateFilter}
            onSelectState={(st) => setStateFilter(st)}
            onNavigateToTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'explorer' && (
          <WorksExplorerView
            anomalies={anomalies}
            loading={loading}
            filters={filters}
            search={search}
            setSearch={setSearch}
            scope={scope}
            setScope={setScope}
            stateFilter={stateFilter}
            setStateFilter={setStateFilter}
            constituencyFilter={constituencyFilter}
            setConstituencyFilter={setConstituencyFilter}
            mpFilter={mpFilter}
            setMpFilter={setMpFilter}
            riskFilter={riskFilter}
            setRiskFilter={setRiskFilter}
            priorityFilter={priorityFilter}
            setPriorityFilter={setPriorityFilter}
            agreementFilter={agreementFilter}
            setAgreementFilter={setAgreementFilter}
            onClearFilters={handleClearFilters}
            onOpenWork={handleOpenWork}
            pagination={pagination}
            onPageChange={handlePageChange}
          />
        )}

        {activeTab === 'detectors' && (
          <DetectorEngineView summary={summary} />
        )}

        {activeTab === 'payments' && (
          <PaymentIntelligenceView overview={overview} />
        )}
      </main>

      {/* Slide-over Forensic Dossier Drawer */}
      <InvestigationDrawer
        work={selectedWork}
        explanation={selectedExplanation}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        loading={drawerLoading}
        onGenerateAI={handleGenerateAI}
        generatingAI={generatingAI}
      />
    </div>
  );
}
