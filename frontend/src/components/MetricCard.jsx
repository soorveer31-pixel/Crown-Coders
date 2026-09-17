import React from 'react';

export default function MetricCard({
  title,
  icon: Icon,
  unit,
  category,
  statusNote,
  accentColor,
  current,
  average,
  total,
  isSelected,
  onClick,
}) {
  const colorMap = {
    yellow: {
      badge: 'text-amber-700 bg-amber-50 border-amber-200/80',
      activeBorder: 'border-amber-500 ring-2 ring-amber-500/15 bg-amber-50/10',
    },
    blue: {
      badge: 'text-sky-700 bg-sky-50 border-sky-200/80',
      activeBorder: 'border-sky-500 ring-2 ring-sky-500/15 bg-sky-50/10',
    },
    emerald: {
      badge: 'text-emerald-700 bg-emerald-50 border-emerald-200/80',
      activeBorder: 'border-emerald-500 ring-2 ring-emerald-500/15 bg-emerald-50/10',
    },
  };

  const scheme = colorMap[accentColor] || colorMap.emerald;

  const formatNum = (num) => {
    if (num === undefined || num === null) return '--';
    return Number(num).toLocaleString(undefined, { maximumFractionDigits: 1 });
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white border rounded-2xl p-6 transition-all duration-200 text-left ${
        onClick ? 'cursor-pointer hover:border-slate-300 hover:shadow-xs' : ''
      } ${isSelected ? scheme.activeBorder : 'border-slate-200/80 shadow-2xs'}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">
            {category}
          </span>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full transition-all ${
              isSelected
                ? 'bg-slate-900 text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {isSelected ? '● Active' : 'Click to View'}
          </span>
        </div>
        <div className={`p-2 rounded-xl border ${scheme.badge}`}>
          <Icon className="w-4 h-4 stroke-[2]" />
        </div>
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        <div className="mt-2 flex items-baseline space-x-2">
          <span className="text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
            {formatNum(current)}
          </span>
          <span className="text-xs font-medium text-slate-400 font-mono">
            {unit} (current)
          </span>
        </div>
      </div>

      <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-2 gap-3 text-xs">
        <div>
          <span className="text-slate-400 block text-[11px]">30d Average:</span>
          <span className="font-semibold text-slate-700 font-mono">
            {formatNum(average)} {unit}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">30d Cumulative:</span>
          <span className="font-semibold text-slate-700 font-mono">
            {formatNum(total)} {unit}
          </span>
        </div>
      </div>

      {statusNote && (
        <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
          <span>Status:</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 font-medium text-slate-600 text-[11px]">
            {statusNote}
          </span>
        </div>
      )}
    </div>
  );
}
