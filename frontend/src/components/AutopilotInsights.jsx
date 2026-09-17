import React, { useState } from 'react';
import {
  Lightbulb,
  AlertTriangle,
  TrendingUp,
  Building2,
  Calendar,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  Wrench,
  Zap,
  Droplets,
  Trash2,
  PlusCircle,
} from 'lucide-react';

export default function AutopilotInsights({
  insightsData,
  loading,
  error,
  resource,
  range,
  onRefresh,
  onCreateIntervention,
}) {
  const [filterType, setFilterType] = useState('all'); // 'all' | 'anomaly' | 'forecast_risk'
  const [createdIds, setCreatedIds] = useState(new Set());

  const allInsights = insightsData?.insights || [];
  const detectedCount = insightsData?.detected_issues_count || 0;
  const upcomingCount = insightsData?.upcoming_risks_count || 0;
  const totalCount = insightsData?.total_insights || 0;

  const filteredInsights = allInsights.filter((item) => {
    if (filterType === 'anomaly') return item.type === 'anomaly';
    if (filterType === 'forecast_risk') return item.type === 'forecast_risk';
    return true;
  });

  const getPriorityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-50 text-rose-700 border-rose-200',
          dot: 'bg-rose-500',
          label: 'Critical Priority',
        };
      case 'HIGH':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          dot: 'bg-amber-500',
          label: 'High Priority',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-sky-50 text-sky-700 border-sky-200',
          dot: 'bg-sky-500',
          label: 'Medium Priority',
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200',
          dot: 'bg-slate-400',
          label: 'Low Priority',
        };
    }
  };

  const getResourceIcon = (res) => {
    switch (res?.toLowerCase()) {
      case 'electricity':
        return <Zap className="w-3.5 h-3.5 text-amber-600" />;
      case 'water':
        return <Droplets className="w-3.5 h-3.5 text-sky-600" />;
      case 'waste':
        return <Trash2 className="w-3.5 h-3.5 text-emerald-600" />;
      default:
        return null;
    }
  };

  const formatDate = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-4 h-4 text-amber-500" />
            <h3 className="text-sm font-bold text-slate-900">
              Autopilot Explain & Recommendation Engine
            </h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              {totalCount} Actionable Directives
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Root-cause explanations and prioritized facility work orders derived from ML anomaly detection and demand forecasts.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Segmented Filter */}
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200/70 text-xs font-medium">
            <button
              onClick={() => setFilterType('all')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                filterType === 'all'
                  ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => setFilterType('anomaly')}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center space-x-1 ${
                filterType === 'anomaly'
                  ? 'bg-white text-rose-800 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <AlertTriangle className="w-3 h-3 text-rose-500" />
              <span>Issues ({detectedCount})</span>
            </button>
            <button
              onClick={() => setFilterType('forecast_risk')}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center space-x-1 ${
                filterType === 'forecast_risk'
                  ? 'bg-white text-sky-800 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <TrendingUp className="w-3 h-3 text-sky-500" />
              <span>Risks ({upcomingCount})</span>
            </button>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              className="text-xs text-slate-600 hover:text-slate-900 inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-amber-600' : ''}`} />
              <span>Refresh</span>
            </button>
          )}
        </div>
      </div>

      {/* Insights Content List */}
      <div className="mt-5">
        {loading ? (
          <div className="py-14 flex flex-col items-center justify-center space-y-2 text-xs text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-600" />
            <span>Generating explanations and facility recommendations...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        ) : filteredInsights.length === 0 ? (
          <div className="py-12 text-center flex flex-col items-center justify-center space-y-1.5">
            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            <p className="text-xs font-semibold text-slate-800">No Action Required</p>
            <p className="text-[11px] text-slate-400 max-w-sm">
              All telemetry and short-term demand projections remain aligned with standard campus baselines.
            </p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[520px] overflow-y-auto pr-1">
            {filteredInsights.map((item, idx) => {
              const priority = getPriorityBadge(item.severity);
              const isAnomaly = item.type === 'anomaly';
              return (
                <div
                  key={item.id || idx}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/30 p-4 hover:bg-slate-50/80 transition-colors"
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${priority.bg}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${priority.dot}`} />
                        <span>{priority.label}</span>
                      </span>

                      <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded-md">
                        {getResourceIcon(item.resource)}
                        <span className="capitalize">{item.resource}</span>
                      </span>

                      <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded-md">
                        <Building2 className="w-3 h-3 text-slate-400" />
                        <span>{item.building}</span>
                      </span>

                      <span
                        className={`text-[10px] font-medium px-2 py-0.5 rounded-md ${
                          isAnomaly
                            ? 'bg-rose-50 text-rose-700'
                            : 'bg-sky-50 text-sky-700'
                        }`}
                      >
                        {isAnomaly ? 'Detected Issue' : 'Upcoming Risk'}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>{formatDate(item.timestamp)}</span>
                      </span>
                      <span className="font-mono text-slate-500">
                        Score: {(item.priority_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Title & Baseline Metrics */}
                  <div className="mt-3">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                      <span>{item.title}</span>
                    </h4>

                    {/* Factual Explanation */}
                    <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                      {item.explanation}
                    </p>

                    {/* Numeric Telemetry Metrics Badge */}
                    <div className="mt-2.5 flex flex-wrap items-center gap-3 text-[11px] bg-white border border-slate-200/70 rounded-lg p-2 font-mono">
                      <div>
                        <span className="text-slate-400">Current Reading: </span>
                        <span className="font-bold text-slate-800">
                          {Number(item.observed_value).toLocaleString()} {item.unit}
                        </span>
                      </div>
                      <div className="border-l border-slate-200 pl-3">
                        <span className="text-slate-400">Normal Level: </span>
                        <span className="text-slate-700">
                          {Number(item.expected_value).toLocaleString()} {item.unit}
                        </span>
                      </div>
                      <div className="border-l border-slate-200 pl-3">
                        <span className="text-slate-400">Difference: </span>
                        <span
                          className={`font-semibold ${
                            item.deviation_percent > 0 ? 'text-rose-600' : 'text-emerald-600'
                          }`}
                        >
                          {item.deviation_percent > 0 ? `+${item.deviation_percent}% higher` : `${item.deviation_percent}%`}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Concrete Actionable Directive Box */}
                  <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-200/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-start space-x-2.5">
                      <Wrench className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                          Recommended Action (What Maintenance Should Do)
                        </span>
                        <p className="text-xs font-medium text-slate-800 mt-0.5 leading-snug">
                          {item.recommended_action}
                        </p>
                      </div>
                    </div>

                    {onCreateIntervention && (
                      <button
                        onClick={async () => {
                          await onCreateIntervention(item);
                          setCreatedIds((prev) => new Set([...prev, item.id]));
                        }}
                        disabled={createdIds.has(item.id)}
                        className={`self-start sm:self-center shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors flex items-center space-x-1.5 ${
                          createdIds.has(item.id)
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200 cursor-default'
                            : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200 shadow-2xs'
                        }`}
                      >
                        {createdIds.has(item.id) ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Intervention Queued</span>
                          </>
                        ) : (
                          <>
                            <PlusCircle className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Create Intervention</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footnote */}
      <div className="mt-3.5 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <span>Transparent Priority Scoring: 0.40 × Score + 0.30 × Dev + 0.20 × OffPeak + 0.10 × Resource</span>
        <span>Deterministic Rule &amp; Heuristic Engine (Zero LLM)</span>
      </div>
    </div>
  );
}
