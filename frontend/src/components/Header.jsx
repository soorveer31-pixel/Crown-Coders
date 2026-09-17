import React from 'react';
import { Leaf, RefreshCw } from 'lucide-react';

export default function Header({ backendHealth, loading, onRefresh }) {
  const isHealthy = backendHealth?.status === 'healthy';

  return (
    <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200/80 flex items-center justify-center text-emerald-600 shadow-2xs">
            <Leaf className="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-slate-900 tracking-tight leading-none">
                Campus Resource Autopilot
              </h1>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600">
                v0.2.0
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              AI Sustainability &amp; Resource Demand Platform
            </p>
          </div>
        </div>

        {/* Status indicator & controls */}
        <div className="flex items-center space-x-2.5">
          {/* Connection Pill */}
          <div
            className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium border ${
              isHealthy
                ? 'bg-emerald-50/80 border-emerald-200 text-emerald-700'
                : 'bg-rose-50 border-rose-200 text-rose-700'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
            <span>{isHealthy ? 'Backend Online' : 'Backend Offline'}</span>
          </div>

          {/* Refresh button */}
          <button
            onClick={onRefresh}
            disabled={loading}
            title="Refresh backend status"
            className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-800 border border-slate-200/70 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
}
