'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { api, ImportResultSummary, ApiError } from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  FileSpreadsheet,
  UploadCloud,
  AlertTriangle,
  Users,
  ArrowRight,
  FileText,
} from 'lucide-react';

export default function ImportsPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ImportResultSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        setError('Invalid file type. Please select a Microsoft Excel file (.xlsx or .xls).');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.importExcel(selectedFile);
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to process Excel file upload.';
        setError(msg);
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Excel Data Import & Ingestion Pipeline"
        subtitle="Batch Student Records Ingestion, Entity Resolution & Field Validation Engine"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Imports' }]}
      />

      {/* Upload Box */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-14 h-14 bg-indigo-50 border border-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4 text-indigo-600">
            <FileSpreadsheet className="w-7 h-7" />
          </div>
          <h2 className="text-base font-bold text-slate-900">Upload Excel Roster (.xlsx / .xls)</h2>
          <p className="text-xs text-slate-500 font-medium mt-1 mb-6">
            The frontend forwards the raw file to the FastAPI backend ingestion service. No browser-side parsing performed.
          </p>

          <form onSubmit={handleUpload} className="space-y-6">
            <div className="relative border-2 border-dashed border-slate-200 hover:border-indigo-500 rounded-2xl p-8 bg-slate-50/50 transition-all text-center group cursor-pointer">
              <input
                type="file"
                accept=".xlsx, .xls"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <UploadCloud className="w-10 h-10 text-slate-400 group-hover:text-indigo-600 transition-colors mx-auto mb-2" />
              {selectedFile ? (
                <div>
                  <span className="inline-flex items-center space-x-1.5 px-3 py-1 bg-indigo-100 text-indigo-800 rounded-lg text-xs font-semibold">
                    <FileText className="w-3.5 h-3.5" />
                    <span>{selectedFile.name}</span>
                  </span>
                  <p className="text-[11px] text-slate-500 mt-1 font-medium">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-semibold text-slate-700">Click or drag Excel file here</p>
                  <p className="text-[11px] text-slate-400 mt-1 font-medium">Supports .xlsx and .xls formats</p>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-bold text-xs rounded-xl shadow-md shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed mx-auto cursor-pointer"
            >
              {uploading ? (
                <span>Ingesting Roster on Backend...</span>
              ) : (
                <>
                  <span>Process Roster & Ingest Students</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Loading State */}
      {uploading && <LoadingState message="FastAPI backend is processing Excel records and resolving student entities..." />}

      {/* Error Alert State */}
      {error && !uploading && <ErrorState message={error} />}

      {/* Structured Import Summary Report */}
      {result && !uploading && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in-50">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-slate-900">Import Summary Report</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800">
                  ID: {result.import_id}
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                    result.status === 'COMPLETED'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {result.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium mt-1">File: {result.filename}</p>
            </div>

            <Link
              href="/students"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs shadow-md shadow-emerald-600/20 transition-all inline-flex items-center space-x-2"
            >
              <Users className="w-4 h-4" />
              <span>View Updated Student Directory</span>
            </Link>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-center">
              <div className="text-[10px] font-bold text-slate-500 uppercase">Total Rows</div>
              <div className="text-lg font-extrabold text-slate-900 mt-1">{result.total_rows}</div>
            </div>

            <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200 text-center">
              <div className="text-[10px] font-bold text-emerald-700 uppercase">Valid Rows</div>
              <div className="text-lg font-extrabold text-emerald-900 mt-1">{result.valid_rows}</div>
            </div>

            <div className="p-3 bg-rose-50 rounded-2xl border border-rose-200 text-center">
              <div className="text-[10px] font-bold text-rose-700 uppercase">Invalid Rows</div>
              <div className="text-lg font-extrabold text-rose-900 mt-1">{result.invalid_rows}</div>
            </div>

            <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200 text-center">
              <div className="text-[10px] font-bold text-amber-700 uppercase">Duplicates</div>
              <div className="text-lg font-extrabold text-amber-900 mt-1">{result.duplicate_rows}</div>
            </div>

            <div className="p-3 bg-indigo-50 rounded-2xl border border-indigo-200 text-center">
              <div className="text-[10px] font-bold text-indigo-700 uppercase">Imported</div>
              <div className="text-lg font-extrabold text-indigo-900 mt-1">{result.imported_students}</div>
            </div>

            <div className="p-3 bg-slate-100 rounded-2xl border border-slate-200 text-center">
              <div className="text-[10px] font-bold text-slate-600 uppercase">Skipped</div>
              <div className="text-lg font-extrabold text-slate-800 mt-1">{result.skipped_students}</div>
            </div>
          </div>

          {/* Errors Breakdown */}
          {result.validation_errors.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Validation Errors Detail ({result.validation_errors.length})</span>
              </h3>
              <div className="border border-slate-200 rounded-2xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                    <tr>
                      <th className="py-2.5 px-4">Row #</th>
                      <th className="py-2.5 px-4">Field</th>
                      <th className="py-2.5 px-4">Issue Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                    {result.validation_errors.map((err, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-2 px-4 font-bold text-slate-900">Row {err.row || idx + 2}</td>
                        <td className="py-2 px-4 font-mono text-[11px] text-indigo-600">{err.field || 'General'}</td>
                        <td className="py-2 px-4 text-rose-600">{err.message || String(err)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
