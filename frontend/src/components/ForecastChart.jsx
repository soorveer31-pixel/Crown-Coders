import React from 'react';
import { TrendingUp, RefreshCw, AlertCircle, Calendar } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export default function ForecastChart({
  forecastData,
  loading,
  error,
  resource,
  onRefresh,
}) {
  const predictions = forecastData?.predictions || [];
  const unit = forecastData?.unit || '';
  const frequency = forecastData?.frequency || 'hourly';
  const horizon = forecastData?.horizon || 24;

  const totalProjected = predictions.reduce((acc, curr) => acc + (curr.predicted_value || 0), 0);
  const avgProjected = predictions.length > 0 ? totalProjected / predictions.length : 0;

  // Resource color themes
  const colorMap = {
    electricity: { stroke: '#f59e0b', fill: '#fef3c7', text: 'text-amber-700' },
    water: { stroke: '#0284c7', fill: '#e0f2fe', text: 'text-sky-700' },
    waste: { stroke: '#10b981', fill: '#d1fae5', text: 'text-emerald-700' },
  };
  const theme = colorMap[resource] || colorMap.electricity;

  const formatTick = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      if (frequency === 'daily') {
        return `${date.getMonth() + 1}/${date.getDate()}`;
      }
      return `${String(date.getHours()).padStart(2, '0')}:00`;
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-900">
              🔮 Tomorrow's Projected Demand (Next {frequency === 'daily' ? `${horizon} Days` : `${horizon} Hours`})
            </h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 capitalize">
              {frequency} AI Model
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Predicts future campus <span className="capitalize font-semibold text-slate-800">{resource}</span> demand so facilities can prepare and prevent costly peak power charges.
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <span className="text-[10px] font-medium text-slate-400 block">Projected Total ({horizon}p)</span>
            <span className="text-xs font-bold text-slate-900">
              {Math.round(totalProjected).toLocaleString()} {unit}
            </span>
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              className="text-xs text-slate-600 hover:text-slate-900 inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
              <span>Update</span>
            </button>
          )}
        </div>
      </div>

      <div className="h-64 w-full pt-4 relative">
        {loading ? (
          <div className="absolute inset-0 bg-white/75 backdrop-blur-2xs z-10 flex items-center justify-center space-x-2 text-slate-600 text-xs font-medium">
            <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
            <span>Generating {horizon}-step demand projections...</span>
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center p-4 max-w-sm">
              <AlertCircle className="w-5 h-5 text-rose-500 mx-auto mb-1.5" />
              <p className="text-xs font-semibold text-slate-800">Forecast Unavailable</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{error}</p>
            </div>
          </div>
        ) : predictions.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400 text-xs">
            No forecast points available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={predictions} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={theme.stroke} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={theme.stroke} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="timestamp"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                tickFormatter={formatTick}
                minTickGap={25}
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
                itemStyle={{ color: theme.stroke, fontWeight: 700, fontSize: '0.85rem' }}
                formatter={(value) => [
                  `${Number(value).toLocaleString()} ${unit}`,
                  'Forecasted Demand',
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
                dataKey="predicted_value"
                stroke={theme.stroke}
                strokeWidth={2}
                strokeDasharray="4 4"
                fillOpacity={1}
                fill="url(#forecastGradient)"
                name="Forecasted Demand"
                isAnimationActive={true}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <span>Average Expected Rate: <strong className="text-slate-700">{Math.round(avgProjected).toLocaleString()} {unit}/{frequency === 'daily' ? 'day' : 'hr'}</strong></span>
        <span>Autoregressive Regressor (Lag & Diurnal Features)</span>
      </div>
    </div>
  );
}
