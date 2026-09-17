import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  FileText,
  Layers,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import { uploadTelemetryCSV, downloadCSVTemplate } from '../services/api';

export default function DataIngestion({ onDataImported }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showErrors, setShowErrors] = useState(false);
  const [showWarnings, setShowWarnings] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.csv')) {
        setError('Please select a valid .csv file.');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
      setResult(null);
    }
  };

  const handleDownloadTemplate = async () => {
    setDownloading(true);
    try {
      await downloadCSVTemplate();
    } catch (err) {
      setError(err.message || 'Failed to download template');
    } finally {
      setDownloading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const summary = await uploadTelemetryCSV(file);
      setResult(summary);
      if (summary.imported_rows > 0 && onDataImported) {
        onDataImported(summary);
      }
    } catch (err) {
      setError(err.message || 'CSV upload failed. Please verify file format.');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <UploadCloud className="w-4 h-4 text-teal-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Upload Campus Data (CSV Ingestion)
            </h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
              Works Without Hardware
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-3xl">
            Any college can upload utility bill spreadsheets to instantly run AI anomaly detection and demand forecasting without expensive IoT meters.
          </p>
        </div>

        {/* Template Download Button */}
        <button
          onClick={handleDownloadTemplate}
          disabled={downloading}
          className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/70 transition-all cursor-pointer shrink-0 disabled:opacity-60"
        >
          {downloading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-600" />
          ) : (
            <Download className="w-3.5 h-3.5 text-slate-600" />
          )}
          <span>Download Sample CSV Template</span>
        </button>
      </div>

      {/* 3-Step Simple Visual Guide */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs bg-teal-50/40 p-3 rounded-xl border border-teal-100/70">
        <div className="flex items-center space-x-2 text-slate-700">
          <span className="w-5 h-5 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0">1</span>
          <span>Download sample CSV template</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-700">
          <span className="w-5 h-5 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0">2</span>
          <span>Select your college's CSV file</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-700">
          <span className="w-5 h-5 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0">3</span>
          <span>Click upload &amp; see live charts update</span>
        </div>
      </div>

      {/* Upload Form Box */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center bg-slate-50/70 p-4 rounded-xl border border-slate-200/60">
        {/* File Selector */}
        <div className="md:col-span-2 flex flex-col sm:flex-row sm:items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv"
            className="hidden"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-white text-slate-800 border border-slate-300 hover:border-teal-500 hover:text-teal-700 shadow-2xs transition-all cursor-pointer"
          >
            <FileSpreadsheet className="w-4 h-4 text-teal-600" />
            <span>Choose CSV File</span>
          </button>

          {file ? (
            <div className="flex items-center space-x-2 text-xs text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium truncate max-w-[220px]">{file.name}</span>
              <span className="text-slate-400 text-[11px]">({formatFileSize(file.size)})</span>
            </div>
          ) : (
            <span className="text-xs text-slate-400">
              No file selected. Required format: <code className="bg-slate-200/60 px-1 py-0.5 rounded text-[11px]">timestamp,building,resource_type,value</code>
            </span>
          )}
        </div>

        {/* Upload Action */}
        <div className="flex justify-start md:justify-end">
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`inline-flex items-center space-x-2 px-5 py-2 rounded-xl text-xs font-bold transition-all ${
              !file || uploading
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-200'
                : 'bg-teal-600 text-white hover:bg-teal-700 shadow-xs cursor-pointer'
            }`}
          >
            {uploading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Validating &amp; Ingesting...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload &amp; Ingest Data</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Top Error Alert */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2.5">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Ingestion Results Panel */}
      {result && (
        <div className="p-4 rounded-xl border border-slate-200/80 bg-white space-y-4 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              {result.invalid_rows === 0 ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-amber-600" />
              )}
              <span className="text-xs font-bold text-slate-900">
                Ingestion Summary: <span className="font-semibold text-slate-600">{result.filename}</span>
              </span>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              {result.message}
            </span>
          </div>

          {/* Metric Chips */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/60">
              <span className="text-[11px] font-medium text-slate-500 block">Total Rows</span>
              <span className="text-base font-bold text-slate-900 mt-0.5 block">{result.total_rows}</span>
            </div>
            <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200/60">
              <span className="text-[11px] font-medium text-emerald-700 block">Valid Rows</span>
              <span className="text-base font-bold text-emerald-800 mt-0.5 block">{result.valid_rows}</span>
            </div>
            <div className="p-3 rounded-lg bg-teal-50/60 border border-teal-200/60">
              <span className="text-[11px] font-medium text-teal-700 block">Imported</span>
              <span className="text-base font-bold text-teal-800 mt-0.5 block">{result.imported_rows}</span>
            </div>
            <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200/60">
              <span className="text-[11px] font-medium text-amber-700 block">Duplicates Skipped</span>
              <span className="text-base font-bold text-amber-800 mt-0.5 block">{result.duplicate_rows}</span>
            </div>
            <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200/60">
              <span className="text-[11px] font-medium text-rose-700 block">Rejected Rows</span>
              <span className="text-base font-bold text-rose-800 mt-0.5 block">{result.invalid_rows}</span>
            </div>
          </div>

          {/* Expandable Rejection Details */}
          {result.errors?.length > 0 && (
            <div className="border border-rose-200 rounded-xl overflow-hidden text-xs">
              <button
                onClick={() => setShowErrors(!showErrors)}
                className="w-full px-3.5 py-2 bg-rose-50/80 text-rose-800 font-semibold flex items-center justify-between hover:bg-rose-100/70 transition-colors cursor-pointer"
              >
                <span>View {result.errors.length} Row Rejection Error(s)</span>
                {showErrors ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
              {showErrors && (
                <div className="p-3 bg-white space-y-1.5 max-h-48 overflow-y-auto border-t border-rose-100 text-rose-700">
                  {result.errors.map((err, idx) => (
                    <div key={idx} className="font-mono text-[11px] flex items-start space-x-1.5">
                      <span className="text-rose-400">•</span>
                      <span>{err}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Expandable Warning Details */}
          {result.warnings?.length > 0 && (
            <div className="border border-amber-200 rounded-xl overflow-hidden text-xs">
              <button
                onClick={() => setShowWarnings(!showWarnings)}
                className="w-full px-3.5 py-2 bg-amber-50/80 text-amber-800 font-semibold flex items-center justify-between hover:bg-amber-100/70 transition-colors cursor-pointer"
              >
                <span>View {result.warnings.length} Duplicate Notice(s)</span>
                {showWarnings ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
              {showWarnings && (
                <div className="p-3 bg-white space-y-1.5 max-h-48 overflow-y-auto border-t border-amber-100 text-amber-700">
                  {result.warnings.map((w, idx) => (
                    <div key={idx} className="font-mono text-[11px] flex items-start space-x-1.5">
                      <span className="text-amber-400">•</span>
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Post-Import Refresh Action */}
          {result.imported_rows > 0 && (
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-xs text-emerald-700 font-medium flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>New readings inserted into database. Pipeline is refreshed.</span>
              </span>
              <button
                onClick={() => onDataImported && onDataImported(result)}
                className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3 h-3 text-slate-500" />
                <span>Re-sync Dashboard</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
