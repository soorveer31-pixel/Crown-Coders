import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap,
  Droplets,
  Trash2,
  Database,
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Cpu,
  Lightbulb,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import MetricCard from '../components/MetricCard';
import AnomalyAlerts from '../components/AnomalyAlerts';
import ForecastChart from '../components/ForecastChart';
import ModelPerformance from '../components/ModelPerformance';
import AutopilotInsights from '../components/AutopilotInsights';
import ImpactMeasurement from '../components/ImpactMeasurement';
import DataIngestion from '../components/DataIngestion';
import {
  getResourceSummary,
  getResourceHistory,
  getAnomalies,
  getForecast,
  getMLEvaluation,
  getInsights,
  createIntervention,
  simulateIntervention,
  completeIntervention,
  getInterventions,
  getImpactSummary,
} from '../services/api';

export default function Dashboard({ backendHealth, loading: healthLoading, error: healthError }) {
  // Simple Guide banner state
  const [showGuide, setShowGuide] = useState(true);

  // Summary metrics state
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState(null);

  // Telemetry chart state
  const [selectedResource, setSelectedResource] = useState('electricity');
  const [selectedRange, setSelectedRange] = useState('7d');
  const [historyData, setHistoryData] = useState(null);
  const [chartLoading, setChartLoading] = useState(true);
  const [chartError, setChartError] = useState(null);

  // ML Anomaly Intelligence state
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [anomaliesLoading, setAnomaliesLoading] = useState(true);
  const [anomaliesError, setAnomaliesError] = useState(null);

  // ML Demand Forecast state
  const [forecastData, setForecastData] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(true);
  const [forecastError, setForecastError] = useState(null);

  // ML Evaluation state
  const [evalData, setEvalData] = useState(null);
  const [evalLoading, setEvalLoading] = useState(true);
  const [evalError, setEvalError] = useState(null);

  // Autopilot Explain & Recommendation state (Milestone 4A)
  const [insightsData, setInsightsData] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [insightsError, setInsightsError] = useState(null);

  // Impact & Savings Measurement state (Milestone 4B)
  const [interventionsData, setInterventionsData] = useState([]);
  const [interventionsLoading, setInterventionsLoading] = useState(true);
  const [interventionsError, setInterventionsError] = useState(null);

  const [impactSummaryData, setImpactSummaryData] = useState(null);
  const [impactSummaryLoading, setImpactSummaryLoading] = useState(true);
  const [impactSummaryError, setImpactSummaryError] = useState(null);

  // 1. Fetch Summary Metrics
  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const data = await getResourceSummary();
      setSummary(data);
    } catch (err) {
      setSummaryError(err.message || 'Failed to load resource summary');
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // 2. Fetch Historical Time Series
  const fetchHistory = useCallback(async (resource, range) => {
    setChartLoading(true);
    setChartError(null);
    try {
      const data = await getResourceHistory(resource, range);
      setHistoryData(data);
    } catch (err) {
      setChartError(err.message || `Failed to load telemetry for ${resource}`);
    } finally {
      setChartLoading(false);
    }
  }, []);

  // 3. Fetch Anomaly Detections
  const fetchAnomalies = useCallback(async (resource, range) => {
    setAnomaliesLoading(true);
    setAnomaliesError(null);
    try {
      const data = await getAnomalies(resource, range);
      setAnomaliesData(data);
    } catch (err) {
      setAnomaliesError(err.message || `Failed to load anomalies for ${resource}`);
    } finally {
      setAnomaliesLoading(false);
    }
  }, []);

  // 4. Fetch Demand Forecast
  const fetchForecast = useCallback(async (resource) => {
    setForecastLoading(true);
    setForecastError(null);
    try {
      const data = await getForecast(resource, 24);
      setForecastData(data);
    } catch (err) {
      setForecastError(err.message || `Failed to load forecast for ${resource}`);
    } finally {
      setForecastLoading(false);
    }
  }, []);

  // 5. Fetch Model Evaluation Benchmarks
  const fetchEval = useCallback(async (resource) => {
    setEvalLoading(true);
    setEvalError(null);
    try {
      const data = await getMLEvaluation(resource);
      setEvalData(data);
    } catch (err) {
      setEvalError(err.message || `Failed to load evaluation for ${resource}`);
    } finally {
      setEvalLoading(false);
    }
  }, []);

  // 6. Fetch Autopilot Explain & Recommendation Insights (Milestone 4A)
  const fetchInsights = useCallback(async (resource, range) => {
    setInsightsLoading(true);
    setInsightsError(null);
    try {
      const data = await getInsights(resource, range);
      setInsightsData(data);
    } catch (err) {
      setInsightsError(err.message || `Failed to load insights for ${resource}`);
    } finally {
      setInsightsLoading(false);
    }
  }, []);

  // 7. Fetch Interventions (Milestone 4B)
  const fetchInterventions = useCallback(async () => {
    setInterventionsLoading(true);
    setInterventionsError(null);
    try {
      const data = await getInterventions();
      setInterventionsData(data);
    } catch (err) {
      setInterventionsError(err.message || 'Failed to load interventions');
    } finally {
      setInterventionsLoading(false);
    }
  }, []);

  // 8. Fetch Impact & Savings Summary (Milestone 4B)
  const fetchImpactSummary = useCallback(async () => {
    setImpactSummaryLoading(true);
    setImpactSummaryError(null);
    try {
      const data = await getImpactSummary();
      setImpactSummaryData(data);
    } catch (err) {
      setImpactSummaryError(err.message || 'Failed to load impact summary');
    } finally {
      setImpactSummaryLoading(false);
    }
  }, []);

  // Handlers for closing the Autopilot loop
  const handleCreateIntervention = async (insightItem) => {
    try {
      await createIntervention(insightItem.id, insightItem.recommended_action);
      await fetchInterventions();
      await fetchImpactSummary();
    } catch (err) {
      console.error('Failed to create intervention:', err);
    }
  };

  const handleSimulateIntervention = async (itvId) => {
    try {
      await simulateIntervention(itvId, 0.85);
      await fetchInterventions();
      await fetchImpactSummary();
    } catch (err) {
      console.error('Failed to simulate intervention:', err);
    }
  };

  const handleCompleteIntervention = async (itvId, afterVal) => {
    try {
      await completeIntervention(itvId, afterVal);
      await fetchInterventions();
      await fetchImpactSummary();
    } catch (err) {
      console.error('Failed to complete intervention:', err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchSummary();
    fetchInterventions();
    fetchImpactSummary();
  }, [fetchSummary, fetchInterventions, fetchImpactSummary]);

  // Refetch telemetry, ML models, and insights whenever resource or range changes
  useEffect(() => {
    fetchHistory(selectedResource, selectedRange);
    fetchAnomalies(selectedResource, selectedRange);
    fetchForecast(selectedResource);
    fetchEval(selectedResource);
    fetchInsights(selectedResource, selectedRange);
  }, [selectedResource, selectedRange, fetchHistory, fetchAnomalies, fetchForecast, fetchEval, fetchInsights]);

  // Synchronize all data
  const handleSyncAll = () => {
    fetchSummary();
    fetchHistory(selectedResource, selectedRange);
    fetchAnomalies(selectedResource, selectedRange);
    fetchForecast(selectedResource);
    fetchEval(selectedResource);
    fetchInsights(selectedResource, selectedRange);
    fetchInterventions();
    fetchImpactSummary();
  };

  // Handle CSV telemetry import (Milestone 5B)
  const handleDataImported = useCallback(() => {
    fetchSummary();
    fetchHistory(selectedResource, selectedRange);
    fetchAnomalies(selectedResource, selectedRange);
    fetchForecast(selectedResource);
    fetchEval(selectedResource);
    fetchInsights(selectedResource, selectedRange);
    fetchImpactSummary();
  }, [
    fetchSummary,
    fetchHistory,
    fetchAnomalies,
    fetchForecast,
    fetchEval,
    fetchInsights,
    fetchImpactSummary,
    selectedResource,
    selectedRange,
  ]);

  // Color config for Recharts according to active resource
  const chartConfig = {
    electricity: {
      color: '#d97706', // amber-600
      gradientId: 'elecGrad',
      label: 'Electricity Demand',
      unit: summary?.electricity?.unit || 'kWh',
    },
    water: {
      color: '#0284c7', // sky-600
      gradientId: 'waterGrad',
      label: 'Water Consumption',
      unit: summary?.water?.unit || 'L',
    },
    waste: {
      color: '#059669', // emerald-600
      gradientId: 'wasteGrad',
      label: 'Waste Generation',
      unit: summary?.waste?.unit || 'kg',
    },
  };

  const currentConfig = chartConfig[selectedResource] || chartConfig.electricity;

  // Format date labels for chart ticks
  const formatTick = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      if (selectedResource === 'waste' || selectedRange === '30d') {
        return `${date.getMonth() + 1}/${date.getDate()}`;
      }
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:00`;
    } catch {
      return isoString;
    }
  };

  const isAnyLoading =
    summaryLoading ||
    chartLoading ||
    anomaliesLoading ||
    forecastLoading ||
    evalLoading ||
    insightsLoading ||
    interventionsLoading ||
    impactSummaryLoading;

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7">
      {/* Top Title & Quick Refresh */}
      <section className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Campus Resource Autopilot
            </h2>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              Live Feed
            </span>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200">
              <Cpu className="w-3 h-3 text-sky-600" />
              <span>AI System Active</span>
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time energy, water, and waste monitoring with AI leak detection, demand predictions, and verified savings.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowGuide(!showGuide)}
            className={`text-xs font-semibold inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border transition-colors ${
              showGuide 
                ? 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100' 
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 shadow-2xs'
            }`}
          >
            <Lightbulb className="w-3.5 h-3.5 text-amber-600" />
            <span>{showGuide ? 'Hide Guide' : '💡 Quick Guide'}</span>
          </button>

          <button
            onClick={handleSyncAll}
            disabled={isAnyLoading}
            className="text-xs font-semibold text-slate-700 hover:text-slate-900 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 shadow-2xs hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isAnyLoading ? 'animate-spin text-emerald-600' : ''}`} />
            <span>Sync Pipeline</span>
          </button>
        </div>
      </section>

      {/* 4-Step Quick Interactive Guide Banner */}
      {showGuide && (
        <section className="bg-gradient-to-r from-amber-500/10 via-sky-500/10 to-emerald-500/10 border border-amber-200/80 rounded-2xl p-5 shadow-xs transition-all">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900">
                How Campus Autopilot Works (In 4 Simple Steps)
              </h3>
            </div>
            <button
              onClick={() => setShowGuide(false)}
              className="text-xs text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              Dismiss ✕
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="bg-white/80 backdrop-blur-xs border border-amber-200/60 rounded-xl p-3">
              <span className="font-bold text-amber-800 block mb-1">1. Track 3 Resources</span>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Live meters monitor Electricity (kWh), Water (L), and Waste (kg) across 5 campus buildings.
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-xs border border-sky-200/60 rounded-xl p-3">
              <span className="font-bold text-sky-800 block mb-1">2. AI Catches Anomalies</span>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Smart AI algorithms instantly detect abnormal spikes, midnight water leaks, and unusual surges.
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-xs border border-purple-200/60 rounded-xl p-3">
              <span className="font-bold text-purple-800 block mb-1">3. Plain English Advice</span>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Translates complex sensor data into a simple checklist explaining what went wrong and how to fix it.
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-xs border border-emerald-200/60 rounded-xl p-3">
              <span className="font-bold text-emerald-800 block mb-1">4. Verify Real Savings</span>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Compares before & after meter readings to prove exact water liters and electricity units saved.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Diagnostics Strip */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-white border border-slate-200/80 rounded-xl p-3.5 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-slate-400 block">Database Layer</span>
            <span className="text-xs font-semibold text-slate-800">SQLite (data/campus.db)</span>
          </div>
          <div className="flex items-center space-x-1 text-xs">
            {backendHealth?.database === 'connected' ? (
              <span className="inline-flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-medium">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                <span>Connected</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md font-medium">
                <AlertCircle className="w-3 h-3 text-rose-600" />
                <span>Disconnected</span>
              </span>
            )}
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-3.5 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-slate-400 block">Intelligence Layer</span>
            <span className="text-xs font-semibold text-slate-800">Isolation Forest + Autoregressive</span>
          </div>
          <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
            Operational
          </span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-3.5 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-slate-400 block">API Endpoints</span>
            <span className="text-xs font-mono text-slate-600">GET /api/ml/*</span>
          </div>
          <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md">
            REST v{backendHealth?.version || '0.2.0'}
          </span>
        </div>
      </section>

      {/* Resource Metrics Cards (3 Pillars) */}
      <section>
        {summaryError && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs mb-4 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{summaryError}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <MetricCard
            title="Electricity Demand"
            category="Power Grid"
            unit={summary?.electricity?.unit || 'kWh'}
            icon={Zap}
            accentColor="yellow"
            current={summary?.electricity?.current}
            average={summary?.electricity?.average}
            total={summary?.electricity?.total}
            isSelected={selectedResource === 'electricity'}
            onClick={() => setSelectedResource('electricity')}
          />
          <MetricCard
            title="Water Consumption"
            category="Hydraulic System"
            unit={summary?.water?.unit || 'L'}
            icon={Droplets}
            accentColor="blue"
            current={summary?.water?.current}
            average={summary?.water?.average}
            total={summary?.water?.total}
            isSelected={selectedResource === 'water'}
            onClick={() => setSelectedResource('water')}
          />
          <MetricCard
            title="Waste Disposal"
            category="Solid Waste"
            unit={summary?.waste?.unit || 'kg'}
            icon={Trash2}
            accentColor="emerald"
            current={summary?.waste?.current}
            average={summary?.waste?.average}
            total={summary?.waste?.total}
            isSelected={selectedResource === 'waste'}
            onClick={() => setSelectedResource('waste')}
          />
        </div>
      </section>

      {/* Data Ingestion & Telemetry Upload (Milestone 5B) */}
      <section>
        <DataIngestion onDataImported={handleDataImported} />
      </section>

      {/* Historical Telemetry Chart (Recharts) */}
      <section className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs">
        {/* Selector Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <span>📊 Campus Resource Usage Over Time</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Showing hourly usage for{' '}
              <span className="text-slate-900 font-semibold capitalize">{selectedResource}</span> ({currentConfig.unit}). Click cards above to switch between Electricity, Water, and Waste.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Resource Selector */}
            <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200/70 text-xs font-medium">
              <button
                onClick={() => setSelectedResource('electricity')}
                className={`px-3 py-1.5 rounded-md transition-all flex items-center space-x-1.5 ${
                  selectedResource === 'electricity'
                    ? 'bg-white text-amber-800 shadow-2xs font-semibold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Electricity</span>
              </button>
              <button
                onClick={() => setSelectedResource('water')}
                className={`px-3 py-1.5 rounded-md transition-all flex items-center space-x-1.5 ${
                  selectedResource === 'water'
                    ? 'bg-white text-sky-800 shadow-2xs font-semibold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Droplets className="w-3.5 h-3.5" />
                <span>Water</span>
              </button>
              <button
                onClick={() => setSelectedResource('waste')}
                className={`px-3 py-1.5 rounded-md transition-all flex items-center space-x-1.5 ${
                  selectedResource === 'waste'
                    ? 'bg-white text-emerald-800 shadow-2xs font-semibold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Waste</span>
              </button>
            </div>

            {/* Range Selector */}
            <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200/70 text-xs font-medium">
              <button
                onClick={() => setSelectedRange('7d')}
                className={`px-2.5 py-1.5 rounded-md transition-all ${
                  selectedRange === '7d'
                    ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setSelectedRange('30d')}
                className={`px-2.5 py-1.5 rounded-md transition-all ${
                  selectedRange === '30d'
                    ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                30 Days
              </button>
            </div>
          </div>
        </div>

        {/* Chart Rendering Area */}
        <div className="h-72 w-full pt-4 relative">
          {chartLoading && (
            <div className="absolute inset-0 bg-white/75 backdrop-blur-2xs z-10 flex items-center justify-center space-x-2 text-slate-600 text-xs font-medium">
              <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
              <span>Loading telemetry for {selectedResource}...</span>
            </div>
          )}

          {chartError ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center p-4 max-w-sm">
                <AlertCircle className="w-6 h-6 text-rose-500 mx-auto mb-1.5" />
                <p className="text-xs font-semibold text-slate-800">Failed to load telemetry</p>
                <p className="text-[11px] text-slate-500 mt-0.5">{chartError}</p>
              </div>
            </div>
          ) : !historyData?.data || historyData.data.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              No historical data points available. Run the seed script to populate data.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={historyData.data}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id={currentConfig.gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={currentConfig.color} stopOpacity={0.18} />
                    <stop offset="95%" stopColor={currentConfig.color} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="timestamp"
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={formatTick}
                  minTickGap={35}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) => Number(val).toLocaleString()}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)',
                    padding: '0.5rem 0.75rem',
                  }}
                  labelStyle={{ color: '#64748b', fontSize: '0.75rem' }}
                  itemStyle={{ color: currentConfig.color, fontWeight: 700, fontSize: '0.85rem' }}
                  formatter={(value) => [
                    `${Number(value).toLocaleString()} ${currentConfig.unit}`,
                    currentConfig.label,
                  ]}
                  labelFormatter={(label) => {
                    try {
                      return new Date(label).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      });
                    } catch {
                      return label;
                    }
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={currentConfig.color}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill={`url(#${currentConfig.gradientId})`}
                  name={currentConfig.label}
                  isAnimationActive={true}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Footnote */}
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>
            Telemetry Source: <code className="text-slate-600 bg-slate-50 px-1.5 py-0.5 rounded font-mono">data/campus.db</code> ({historyData?.data?.length || 0} readings)
          </span>
          <span className="text-slate-400">
            30-day realistic occupancy simulation
          </span>
        </div>
      </section>

      {/* Predictive Modeling & Anomaly Intelligence Layer */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Short-Term Demand Forecast */}
        <ForecastChart
          forecastData={forecastData}
          loading={forecastLoading}
          error={forecastError}
          resource={selectedResource}
          onRefresh={() => fetchForecast(selectedResource)}
        />

        {/* Anomaly Alerts */}
        <AnomalyAlerts
          anomaliesData={anomaliesData}
          loading={anomaliesLoading}
          error={anomaliesError}
          resource={selectedResource}
          range={selectedRange}
          onRefresh={() => fetchAnomalies(selectedResource, selectedRange)}
        />
      </section>

      {/* Autopilot Explain & Recommendation Engine (Milestone 4A) */}
      <section>
        <AutopilotInsights
          insightsData={insightsData}
          loading={insightsLoading}
          error={insightsError}
          resource={selectedResource}
          range={selectedRange}
          onRefresh={() => fetchInsights(selectedResource, selectedRange)}
          onCreateIntervention={handleCreateIntervention}
        />
      </section>

      {/* Impact & Savings Measurement Layer (Milestone 4B) */}
      <section>
        <ImpactMeasurement
          impactSummary={impactSummaryData}
          interventions={interventionsData}
          loading={interventionsLoading || impactSummaryLoading}
          error={interventionsError || impactSummaryError}
          onRefresh={() => {
            fetchInterventions();
            fetchImpactSummary();
          }}
          onSimulate={handleSimulateIntervention}
          onComplete={handleCompleteIntervention}
        />
      </section>

      {/* Model Verification & Evaluation Benchmarks */}
      <section>
        <ModelPerformance
          evalData={evalData}
          loading={evalLoading}
          error={evalError}
          resource={selectedResource}
        />
      </section>
    </main>
  );
}
