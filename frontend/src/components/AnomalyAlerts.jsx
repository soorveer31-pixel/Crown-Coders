import React from 'react';
import { AlertTriangle, CheckCircle2, AlertCircle, RefreshCw, Building2 } from 'lucide-react';

export default function AnomalyAlerts({
  anomaliesData,
  loading,
  error,
  resource,
  range,
  onRefresh,
}) {
  const anomalies = anomaliesData?.anomalies || [];
  const total = anomaliesData?.total_anomalies || 0;
  const unit = anomaliesData?.unit || '';

  const getSeverityBadge = (score) => {
    if (score >= 0.75) {
      return {
        label: 'Critical Surge',
        bg: 'bg-rose-50 text-rose-700 border-rose-200',
        dot: 'bg-rose-500',
      };
    }
    if (score >= 0.5) {
      return {
        label: 'High Deviation',
        bg: 'bg-amber-50 text-amber-700 border-amber-200',
        dot: 'bg-amber-500',
      };
    }
    return {
      label: 'Elevated Outlier',
      bg: 'bg-slate-100 text-slate-700 border-slate-200',
      dot: 'bg-slate-400',
    };
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Unusual Spikes &amp; Leaks (AI Anomaly Alerts)
            </h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
              {total} Issues Found
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            AI scans every campus meter and automatically flags readings that are abnormally high in <span className="capitalize font-semibold text-slate-800">{resource}</span> ({range}).
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            className="self-start sm:self-auto text-xs text-slate-600 hover:text-slate-900 inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-amber-600' : ''}`} />
            <span>Rescan</span>
          </button>
        )}
      </div>

      <div className="mt-4">
        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center space-y-2 text-xs text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-600" />
            <span>Scanning telemetry with Isolation Forest...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        ) : anomalies.length === 0 ? (
          <div className="py-10 text-center flex flex-col items-center justify-center space-y-1.5">
            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            <p className="text-xs font-semibold text-slate-800">Nominal Consumption Baseline</p>
            <p className="text-[11px] text-slate-400 max-w-sm">
              No anomalies detected in the selected {range} window for {resource}. All readings remain within expected diurnal variations.
            </p>
          </div>
        ) : (
          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {anomalies.map((anom, idx) => {
              const severity = getSeverityBadge(anom.anomaly_score);
              return (
                <div
                  key={`${anom.timestamp}-${idx}`}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors gap-2"
                >
                  <div className="flex items-start space-x-3">
                    <div className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 mt-0.5">
                      <Building2 className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-slate-900">
                          {anom.building_name || 'Campus Meter'}
                        </span>
                        <span
                          className={`inline-flex items-center space-x-1 text-[10px] font-medium px-2 py-0.5 rounded-full border ${severity.bg}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${severity.dot}`} />
                          <span>{severity.label}</span>
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block mt-0.5">
                        Timestamp: {formatDate(anom.timestamp)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end space-x-4 pl-9 sm:pl-0">
                    <div className="text-left sm:text-right">
                      <span className="text-[10px] font-medium text-slate-400 block">Spike Reading</span>
                      <span className="text-xs font-bold text-slate-900">
                        {Number(anom.value).toLocaleString()} {unit}
                      </span>
                    </div>
                    <div className="text-left sm:text-right border-l border-slate-200 pl-3">
                      <span className="text-[10px] font-medium text-slate-400 block">AI Confidence</span>
                      <span className="text-xs font-mono font-semibold text-amber-700">
                        {(anom.anomaly_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span>AI Engine: Scikit-learn Isolation Forest</span>
        <span>Identifies leaks automatically without manual threshold guessing</span>
      </div>
    </div>
  );
}
