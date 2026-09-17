import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import { checkBackendHealth } from './services/api';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
          <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 p-6 shadow-sm text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto text-xl font-bold">
              !
            </div>
            <h2 className="text-base font-bold text-slate-900">Dashboard Rendering Notice</h2>
            <p className="text-xs text-slate-500 font-mono bg-slate-100 p-3 rounded-lg text-left overflow-auto max-h-32">
              {this.state.error?.message || String(this.state.error)}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-emerald-600 text-white text-xs font-semibold rounded-xl hover:bg-emerald-700 transition-colors cursor-pointer"
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [backendHealth, setBackendHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkBackendHealth();
      setBackendHealth(data);
    } catch (err) {
      setError(err.message || 'Could not connect to FastAPI server');
      setBackendHealth({ status: 'offline' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-50/60 text-slate-800 flex flex-col antialiased">
        <Header
          backendHealth={backendHealth}
          loading={loading}
          onRefresh={fetchHealth}
        />
        <div className="flex-1">
          <Dashboard
            backendHealth={backendHealth}
            loading={loading}
            error={error}
          />
        </div>
        <footer className="border-t border-slate-200/60 bg-white/80 py-5 text-center text-xs text-slate-400">
          Campus Resource Autopilot &copy; {new Date().getFullYear()} &bull; Sustainability Telemetry Platform
        </footer>
      </div>
    </ErrorBoundary>
  );
}
