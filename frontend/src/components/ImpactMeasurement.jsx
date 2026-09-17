import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Zap,
  Droplets,
  Trash2,
  TrendingDown,
  Wrench,
  Sparkles,
  ArrowRight,
  Clock,
  FlaskConical,
  ShieldCheck,
} from 'lucide-react';

export default function ImpactMeasurement({
  impactSummary,
  interventions,
  loading,
  error,
  onRefresh,
  onSimulate,
  onComplete,
}) {
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'COMPLETED' | 'PLANNED'
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const filteredInterventions = (interventions || []).filter((itv) => {
    if (statusFilter === 'COMPLETED') return itv.status === 'COMPLETED';
    if (statusFilter === 'PLANNED') return itv.status === 'PLANNED';
    return true;
  });

  const handleSimulateClick = async (id) => {
    setActionLoadingId(id);
    try {
      await onSimulate(id);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCompleteClick = async (id) => {
    setActionLoadingId(id);
    try {
      await onComplete(id);
    } finally {
      setActionLoadingId(null);
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
    if (!isoString) return '—';
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
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <TrendingDown className="w-4 h-4 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-900">
              💰 Verified Resource Savings &amp; Maintenance Actions
            </h3>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              <span>Full Loop Closed</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Verifies how much water, electricity, and waste was actually saved after campus maintenance fixes an issue.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Status Filter */}
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200/70 text-xs font-medium">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                statusFilter === 'all'
                  ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              All ({interventions?.length || 0})
            </button>
            <button
              onClick={() => setStatusFilter('PLANNED')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                statusFilter === 'PLANNED'
                  ? 'bg-white text-amber-800 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Planned
            </button>
            <button
              onClick={() => setStatusFilter('COMPLETED')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                statusFilter === 'COMPLETED'
                  ? 'bg-white text-emerald-800 shadow-2xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Completed
            </button>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              className="text-xs text-slate-600 hover:text-slate-900 inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
              <span>Refresh</span>
            </button>
          )}
        </div>
      </div>

      {/* Mandatory Transparent Disclaimer Banner */}
      <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 flex items-start space-x-2.5 text-xs text-amber-900">
        <FlaskConical className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold text-amber-950 flex items-center space-x-1">
            <span>DEMONSTRATION IMPACT MEASUREMENT</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-amber-200 text-amber-900 rounded">
              SIMULATED MODE
            </span>
          </span>
          <p className="text-[11px] text-amber-800 leading-relaxed">
            Values marked <span className="font-semibold text-amber-900">SIMULATED DEMO</span> reflect transparent reduction models (mitigating 85% of anomalous excess consumption) because the prototype environment operates on simulated campus telemetry without live physical actuators. Physical telemetry ingestion is fully supported via <span className="font-semibold text-amber-900">MEASURED</span> mode.
          </p>
        </div>
      </div>

      {/* 3 Pillar Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Electricity Impact */}
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/40 p-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 flex items-center space-x-1">
              <Zap className="w-3.5 h-3.5 text-amber-600" />
              <span>Electricity Reduction</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
              kWh
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-slate-900">
              {loading ? '...' : Number(impactSummary?.electricity?.total_estimated_savings || 0).toLocaleString()}
            </span>
            <span className="text-xs font-semibold text-slate-500">kWh saved</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500">
            <span>Avg Improvement:</span>
            <span className="font-semibold text-emerald-600 font-mono">
              {loading ? '...' : `+${impactSummary?.electricity?.average_improvement_percent || 0}%`}
            </span>
          </div>
        </div>

        {/* Water Impact */}
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/40 p-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 flex items-center space-x-1">
              <Droplets className="w-3.5 h-3.5 text-sky-600" />
              <span>Water Conservation</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
              Liters (L)
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-slate-900">
              {loading ? '...' : Number(impactSummary?.water?.total_estimated_savings || 0).toLocaleString()}
            </span>
            <span className="text-xs font-semibold text-slate-500">L saved</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500">
            <span>Avg Improvement:</span>
            <span className="font-semibold text-emerald-600 font-mono">
              {loading ? '...' : `+${impactSummary?.water?.average_improvement_percent || 0}%`}
            </span>
          </div>
        </div>

        {/* Waste Impact */}
        <div className="rounded-xl border border-slate-200/80 bg-slate-50/40 p-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500 flex items-center space-x-1">
              <Trash2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Waste Diverted</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
              kg
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-slate-900">
              {loading ? '...' : Number(impactSummary?.waste?.total_estimated_savings || 0).toLocaleString()}
            </span>
            <span className="text-xs font-semibold text-slate-500">kg diverted</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500">
            <span>Avg Improvement:</span>
            <span className="font-semibold text-emerald-600 font-mono">
              {loading ? '...' : `+${impactSummary?.waste?.average_improvement_percent || 0}%`}
            </span>
          </div>
        </div>
      </div>

      {/* Interventions Execution List */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Logged Interventions &amp; Verifications
          </h4>
          <span className="text-[11px] text-slate-400">
            {filteredInterventions.length} items logged
          </span>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs mb-3 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center space-y-2 text-xs text-slate-500 border border-dashed border-slate-200 rounded-xl bg-slate-50/20">
            <RefreshCw className="w-5 h-5 animate-spin text-emerald-600" />
            <span>Loading facility interventions and aggregate savings...</span>
          </div>
        ) : filteredInterventions.length === 0 ? (
          <div className="py-10 text-center flex flex-col items-center justify-center space-y-2 border border-dashed border-slate-200 rounded-xl bg-slate-50/30">
            <Wrench className="w-6 h-6 text-slate-400" />
            <p className="text-xs font-semibold text-slate-700">No Interventions in this View</p>
            <p className="text-[11px] text-slate-400 max-w-sm">
              Click <span className="font-semibold text-slate-600">"Create Intervention"</span> on any insight card above to initiate a maintenance ticket and test the Autopilot measurement loop.
            </p>
          </div>
        ) : (
          <div className="space-y-3.5 max-h-[500px] overflow-y-auto pr-1">
            {filteredInterventions.map((itv) => {
              const isCompleted = itv.status === 'COMPLETED';
              const isSimulated = itv.measurement_type === 'SIMULATED';
              const isActionLoading = actionLoadingId === itv.id;

              return (
                <div
                  key={itv.id}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/30 p-4 hover:bg-slate-50/80 transition-colors"
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
                    <div className="flex flex-wrap items-center gap-2">
                      {/* Status Badge */}
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                          isCompleted
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {itv.status}
                      </span>

                      {/* Measurement Type Badge */}
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${
                          isSimulated
                            ? 'bg-amber-50 text-amber-800 border-amber-200'
                            : 'bg-sky-50 text-sky-800 border-sky-200'
                        }`}
                      >
                        {isSimulated ? 'SIMULATED DEMO' : 'MEASURED'}
                      </span>

                      {/* Resource */}
                      <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded-md">
                        {getResourceIcon(itv.resource_type)}
                        <span className="capitalize">{itv.resource_type}</span>
                      </span>

                      {/* Building */}
                      <span className="text-[11px] font-medium text-slate-700 bg-white border border-slate-200 px-2 py-0.5 rounded-md">
                        {itv.building_name}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{formatDate(itv.created_at)}</span>
                    </div>
                  </div>

                  {/* Action Description */}
                  <div className="mt-2.5">
                    <div className="flex items-start space-x-2">
                      <Wrench className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                      <p className="text-xs font-semibold text-slate-800 leading-snug">
                        {itv.action}
                      </p>
                    </div>
                  </div>

                  {/* Before -> After Comparison Strip */}
                  <div className="mt-3 p-3 rounded-lg bg-white border border-slate-200/70 grid grid-cols-1 sm:grid-cols-3 gap-3 items-center text-xs">
                    {/* Before */}
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Before Fix (Leak/Spike)
                      </span>
                      <div className="flex items-baseline space-x-1.5 mt-0.5">
                        <span className="font-bold text-slate-900 font-mono">
                          {Number(itv.before_value).toLocaleString()}
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">{itv.unit}</span>
                      </div>
                      <span className="text-[10px] text-slate-400">
                        Normal Level: {Number(itv.baseline_value).toLocaleString()} {itv.unit}
                      </span>
                    </div>

                    {/* Arrow / Transition */}
                    <div className="sm:text-center flex sm:flex-col items-center justify-center space-x-2 sm:space-x-0">
                      <ArrowRight className="w-4 h-4 text-emerald-600" />
                      <span className="text-[10px] font-medium text-emerald-700">
                        {isCompleted ? 'Repaired & Verified' : 'Action In Progress'}
                      </span>
                    </div>

                    {/* After & Savings */}
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        After Fix (Verified Result)
                      </span>
                      {isCompleted ? (
                        <div>
                          <div className="flex items-baseline space-x-1.5 mt-0.5">
                            <span className="font-bold text-emerald-700 font-mono">
                              {Number(itv.after_value).toLocaleString()}
                            </span>
                            <span className="text-[11px] text-slate-500 font-mono">{itv.unit}</span>
                          </div>
                          <div className="flex items-center space-x-1.5 text-[11px] text-emerald-600 font-semibold font-mono">
                            <span>Saved: {Number(itv.estimated_savings).toLocaleString()} {itv.unit}</span>
                            <span>(-{itv.savings_percentage}%)</span>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-1 text-slate-400 text-[11px] italic">
                          Awaiting repair completion...
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions Footer */}
                  {!isCompleted && (
                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-end space-x-2.5">
                      <button
                        onClick={() => handleSimulateClick(itv.id)}
                        disabled={isActionLoading}
                        className="text-xs font-semibold text-amber-900 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-3.5 py-1.5 rounded-lg transition-colors flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                      >
                        {isActionLoading ? (
                          <RefreshCw className="w-3 h-3 animate-spin text-amber-600" />
                        ) : (
                          <Sparkles className="w-3 h-3 text-amber-600" />
                        )}
                        <span>Simulate Fix &amp; Calculate Savings</span>
                      </button>

                      <button
                        onClick={() => handleCompleteClick(itv.id)}
                        disabled={isActionLoading}
                        className="text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                      >
                        <ShieldCheck className="w-3 h-3 text-emerald-600" />
                        <span>Mark as Fixed</span>
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Note */}
      <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <span>Comparable Baseline: Median of non-anomalous historical readings (same hour &amp; day profile)</span>
        <span>Transparent Mitigation Factor: 85% excess resolved</span>
      </div>
    </div>
  );
}
