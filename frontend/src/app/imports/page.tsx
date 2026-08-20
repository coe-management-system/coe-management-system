'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  FileSpreadsheet,
  UploadCloud,
  Users,
  ArrowRight,
  FileText,
  CheckCircle2,
  Database,
  PlusCircle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

interface PreviewData {
  import_id: number | string;
  filename: string;
  mapping: Record<string, string>;
  unmapped_columns: string[];
  ambiguous_columns: string[];
  summary: {
    total_rows: number;
    valid: number;
    invalid: number;
    reference_errors: number;
    existing: number;
    duplicates: number;
    ready_to_commit: number;
  };
  records: Array<Record<string, unknown>>;
  attendance?: {
    format?: string | null;
    detected_type?: string | null;
    reason?: string | null;
    subject?: string | null;
    subject_source?: string | null;
    issues: Array<Record<string, unknown>>;
  };
}

interface AttendanceCommitResult {
  inserted: number;
  updated: number;
  overwritten: Array<Record<string, unknown>>;
  excluded_events: number;
  below_threshold_count: number;
  below_threshold: Array<Record<string, unknown>>;
}

export default function ImportsPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importType, setImportType] = useState<string>('attendance');
  const [subject, setSubject] = useState<string>('');
  const [step, setStep] = useState<'upload' | 'preview' | 'committed'>('upload');
  const [validating, setValidating] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [committedResult, setCommittedResult] = useState<{ imported_count: number; import_id: number | string; attendance?: AttendanceCommitResult | null } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls') && !file.name.endsWith('.csv')) {
        setError('Invalid file type. Please select a Microsoft Excel file (.xlsx or .xls) or a .csv file.');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError(null);
      setPreview(null);
      setCommittedResult(null);
      setStep('upload');
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setValidating(true);
    setError(null);

    try {
      const res = await api.validateExcel(selectedFile, importType, subject.trim() || undefined);
      setPreview(res);
      setStep('preview');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to analyze Excel file.';
        setError(msg);
      }
    } finally {
      setValidating(false);
    }
  };

  const handleCommit = async () => {
    if (!preview) return;

    setCommitting(true);
    setError(null);

    try {
      const res = await api.commitExcel(preview.import_id);
      setCommittedResult({
        imported_count: res.imported_count,
        import_id: res.import_id,
        attendance: res.attendance,
      });
      setStep('committed');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to commit import to database.';
        setError(msg);
      }
    } finally {
      setCommitting(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreview(null);
    setCommittedResult(null);
    setError(null);
    setStep('upload');
  };

  const handleExport = async () => {
    if (!preview) return;
    setExporting(true);
    setError(null);
    try {
      await api.downloadAttendanceExport(preview.import_id);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to export attendance sheet.');
      }
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Excel Data Import & Ingestion Pipeline"
        subtitle="Batch Student Records Ingestion, Entity Resolution & Field Validation Engine"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Imports' }]}
      />

      {/* Progress Steps Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
        <div className="flex items-center justify-around text-xs font-bold">
          <div className={`flex items-center space-x-2 ${step === 'upload' ? 'text-indigo-600' : 'text-emerald-600'}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs text-white ${step === 'upload' ? 'bg-indigo-600' : 'bg-emerald-600'}`}>
              1
            </div>
            <span>Upload File</span>
          </div>
          <div className="w-12 h-0.5 bg-slate-200" />
          <div className={`flex items-center space-x-2 ${step === 'preview' ? 'text-indigo-600' : step === 'committed' ? 'text-emerald-600' : 'text-slate-400'}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs text-white ${step === 'preview' ? 'bg-indigo-600' : step === 'committed' ? 'bg-emerald-600' : 'bg-slate-300'}`}>
              2
            </div>
            <span>Review & Columns Check</span>
          </div>
          <div className="w-12 h-0.5 bg-slate-200" />
          <div className={`flex items-center space-x-2 ${step === 'committed' ? 'text-emerald-600' : 'text-slate-400'}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs text-white ${step === 'committed' ? 'bg-emerald-600' : 'bg-slate-300'}`}>
              3
            </div>
            <span>Saved to Database</span>
          </div>
        </div>
      </div>

      {/* STEP 1: Upload Box */}
      {step === 'upload' && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs">
          <div className="max-w-2xl mx-auto text-center">
            <div className="w-14 h-14 bg-indigo-50 border border-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4 text-indigo-600">
              <FileSpreadsheet className="w-7 h-7" />
            </div>
            <h2 className="text-base font-bold text-slate-900">Upload Excel Dataset (.xlsx / .xls / .csv)</h2>
            <p className="text-xs text-slate-500 font-medium mt-1 mb-6">
              The engine will analyze columns, auto-detect extra fields, and let you preview before saving permanently.
            </p>

            <form onSubmit={handleAnalyze} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Import Type</label>
                  <select
                    value={importType}
                    onChange={(e) => setImportType(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500"
                  >
                    <option value="attendance">Attendance</option>
                    <option value="students">Students</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 mb-1.5 uppercase tracking-wide">
                    Subject (for attendance)
                  </label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="e.g. MATH101"
                    className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="relative border-2 border-dashed border-slate-200 hover:border-indigo-500 rounded-2xl p-8 bg-slate-50/50 transition-all text-center group cursor-pointer">
                <input
                  type="file"
                  accept=".xlsx, .xls, .csv"
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
                    <p className="text-xs font-semibold text-slate-700">Click or drag file here</p>
                    <p className="text-[11px] text-slate-400 mt-1 font-medium">Supports .xlsx, .xls and .csv formats</p>
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={!selectedFile || validating}
                className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-bold text-xs rounded-xl shadow-md shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed mx-auto cursor-pointer"
              >
                {validating ? (
                  <span>Analyzing Dataset Columns & Records...</span>
                ) : (
                  <>
                    <span>Analyze & Preview Roster</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Loading States */}
      {validating && <LoadingState message="FastAPI backend is analyzing Excel columns, resolving entities, and running validation..." />}
      {committing && <LoadingState message="Permanently writing records to the database transaction..." />}

      {/* Error Alert State */}
      {error && !validating && !committing && <ErrorState message={error} />}

      {/* STEP 2: Preview & Interactive Confirmation */}
      {step === 'preview' && preview && !validating && !committing && (
        <div className="space-y-6 animate-in fade-in-50">
          {/* Confirmation Callout Banner */}
          <div className="p-5 bg-gradient-to-r from-amber-500/10 via-indigo-500/10 to-emerald-500/10 border-2 border-indigo-300 rounded-3xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-indigo-600 text-white rounded-xl mt-0.5">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Ready to Commit {preview.summary.ready_to_commit} Record(s) to Database
                </h3>
                <p className="text-xs text-slate-600 mt-1">
                  File: <strong className="text-slate-800">{preview.filename}</strong> (Import #{preview.import_id}).
                  {preview.unmapped_columns.length > 0 && (
                    <span className="text-amber-800 font-medium ml-1">
                      Extra columns detected: [{preview.unmapped_columns.join(', ')}].
                    </span>
                  )}
                  {' '}Review the analysis below before permanently saving.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 shrink-0">
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs transition-all flex items-center space-x-1.5 cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Cancel</span>
              </button>
              <button
                type="button"
                onClick={handleCommit}
                disabled={preview.summary.ready_to_commit === 0}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs shadow-md shadow-emerald-600/30 transition-all flex items-center space-x-2 disabled:opacity-50 cursor-pointer"
              >
                <Database className="w-4 h-4" />
                <span>Confirm & Commit to Database</span>
              </button>
            </div>
          </div>

          {/* Metric Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-center">
              <div className="text-[10px] font-bold text-slate-500 uppercase">Total Rows</div>
              <div className="text-lg font-extrabold text-slate-900 mt-1">{preview.summary.total_rows}</div>
            </div>

            <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200 text-center">
              <div className="text-[10px] font-bold text-emerald-700 uppercase">Valid Rows</div>
              <div className="text-lg font-extrabold text-emerald-900 mt-1">{preview.summary.valid}</div>
            </div>

            <div className="p-3 bg-rose-50 rounded-2xl border border-rose-200 text-center">
              <div className="text-[10px] font-bold text-rose-700 uppercase">Invalid Rows</div>
              <div className="text-lg font-extrabold text-rose-900 mt-1">{preview.summary.invalid}</div>
            </div>

            <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200 text-center">
              <div className="text-[10px] font-bold text-amber-700 uppercase">Duplicates</div>
              <div className="text-lg font-extrabold text-amber-900 mt-1">{preview.summary.duplicates}</div>
            </div>

            <div className="p-3 bg-blue-50 rounded-2xl border border-blue-200 text-center">
              <div className="text-[10px] font-bold text-blue-700 uppercase">Already Existing</div>
              <div className="text-lg font-extrabold text-blue-900 mt-1">{preview.summary.existing}</div>
            </div>

            <div className="p-3 bg-indigo-50 rounded-2xl border border-indigo-200 text-center">
              <div className="text-[10px] font-bold text-indigo-700 uppercase">Ready to Commit</div>
              <div className="text-lg font-extrabold text-indigo-900 mt-1">{preview.summary.ready_to_commit}</div>
            </div>
          </div>

          {/* Attendance Import Summary Card */}
          {preview.attendance && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
              <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Attendance Import Analysis</span>
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200">
                  <div className="text-[10px] font-bold text-slate-500 uppercase">Detected Format</div>
                  <div className="text-sm font-extrabold text-slate-900 mt-1 capitalize">
                    {preview.attendance.format || '—'}
                  </div>
                  {preview.attendance.reason && (
                    <div className="text-[10px] text-slate-500 mt-0.5 font-medium">{preview.attendance.reason}</div>
                  )}
                </div>
                <div className="p-3 bg-indigo-50 rounded-2xl border border-indigo-200">
                  <div className="text-[10px] font-bold text-indigo-700 uppercase">Subject</div>
                  <div className="text-sm font-extrabold text-indigo-900 mt-1">
                    {preview.attendance.subject || '—'}
                  </div>
                  <div className="text-[10px] text-indigo-600 mt-0.5 font-medium capitalize">
                    {preview.attendance.subject_source === 'explicit' ? 'from form' : (preview.attendance.subject_source || '')}
                  </div>
                </div>
                <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200">
                  <div className="text-[10px] font-bold text-amber-700 uppercase">Data Issues Flagged</div>
                  <div className="text-sm font-extrabold text-amber-900 mt-1">
                    {preview.attendance.issues?.length ?? 0}
                  </div>
                  <div className="text-[10px] text-amber-600 mt-0.5 font-medium">not committed until fixed</div>
                </div>
                <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200">
                  <div className="text-[10px] font-bold text-emerald-700 uppercase">Events Ready</div>
                  <div className="text-sm font-extrabold text-emerald-900 mt-1">{preview.summary.ready_to_commit}</div>
                  <div className="text-[10px] text-emerald-600 mt-0.5 font-medium">will update student records</div>
                </div>
              </div>

              {preview.attendance.issues && preview.attendance.issues.length > 0 && (
                <div className="p-4 bg-amber-50/60 rounded-2xl border border-amber-200 space-y-2">
                  <div className="font-bold text-amber-900 text-[11px]">Flagged issues in this sheet (rows were excluded, nothing auto-created)</div>
                  <ul className="space-y-1.5 max-h-40 overflow-y-auto">
                    {preview.attendance.issues.slice(0, 20).map((issue, idx) => (
                      <li key={idx} className="text-[11px] text-amber-800 font-medium flex items-start space-x-2">
                        <span className="px-1.5 py-0.5 bg-amber-100 text-amber-900 rounded text-[10px] font-bold shrink-0">
                          R{String(issue.row ?? '?')}
                        </span>
                        <span className="break-words">{String(issue.message || JSON.stringify(issue))}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Column Mapping & Extra Columns Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
              <Database className="w-4 h-4 text-indigo-600" />
              <span>Column Mapping & Schema Discovery</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                <div className="font-bold text-slate-700">Mapped Database Columns ({Object.keys(preview.mapping).length})</div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(preview.mapping).map(([raw, canonical]) => (
                    <span key={raw} className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-[11px] font-semibold text-slate-800 shadow-2xs">
                      {raw} &rarr; <span className="text-indigo-600">{canonical}</span>
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-amber-50/60 rounded-2xl border border-amber-200 space-y-2">
                <div className="font-bold text-amber-900 flex items-center space-x-1.5">
                  <PlusCircle className="w-3.5 h-3.5 text-amber-600" />
                  <span>Extra / Unmapped Columns in File ({preview.unmapped_columns.length})</span>
                </div>
                {preview.unmapped_columns.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {preview.unmapped_columns.map((col) => (
                      <span key={col} className="px-2.5 py-1 bg-white border border-amber-300 rounded-lg text-[11px] font-semibold text-amber-800 shadow-2xs">
                        {col}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-[11px]">No extra unmapped columns found.</p>
                )}
              </div>
            </div>
          </div>

          {/* Sample Records Preview Table */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-slate-900">
              Record Preview (Showing first {Math.min(5, preview.records.length)} of {preview.summary.total_rows})
            </h3>
            <div className="border border-slate-200 rounded-2xl overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                  <tr>
                    <th className="py-2.5 px-4">Row #</th>
                    <th className="py-2.5 px-4">Category</th>
                    <th className="py-2.5 px-4">Admission / Roll</th>
                    <th className="py-2.5 px-4">Name</th>
                    <th className="py-2.5 px-4">Email</th>
                    <th className="py-2.5 px-4">Branch / Dept</th>
                    <th className="py-2.5 px-4">Batch</th>
                    <th className="py-2.5 px-4">Group</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                  {preview.records.slice(0, 5).map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="py-2 px-4 font-bold text-slate-900">Row {r.row ? String(r.row) : idx + 2}</td>
                      <td className="py-2 px-4">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                          r.category === 'VALID' ? 'bg-emerald-100 text-emerald-800' :
                          r.category === 'DUPLICATE' ? 'bg-amber-100 text-amber-800' :
                          r.category === 'EXISTING' ? 'bg-blue-100 text-blue-800' : 'bg-rose-100 text-rose-800'
                        }`}>
                          {String(r.category || 'VALID')}
                        </span>
                      </td>
                      <td className="py-2 px-4 font-mono text-[11px] text-indigo-600">{String(r.roll_no || '-')}</td>
                      <td className="py-2 px-4">{String(r.name || '-')}</td>
                      <td className="py-2 px-4 text-slate-500">{String(r.email || '-')}</td>
                      <td className="py-2 px-4">{String(r.department || '-')}</td>
                      <td className="py-2 px-4">{String(r.batch || '-')}</td>
                      <td className="py-2 px-4">{String(r.group || '-')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Committed Success Report */}
      {step === 'committed' && committedResult && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in-50">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-emerald-100 text-emerald-700 rounded-2xl flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-slate-900">Successfully Imported to Database</span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    ID: {committedResult.import_id}
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  {committedResult.imported_count} records committed permanently to the database.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs transition-all flex items-center space-x-1.5 cursor-pointer"
              >
                <UploadCloud className="w-4 h-4" />
                <span>Import Another File</span>
              </button>
              <Link
                href="/students"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs shadow-md shadow-emerald-600/20 transition-all inline-flex items-center space-x-2"
              >
                <Users className="w-4 h-4" />
                <span>View Student Directory</span>
              </Link>
            </div>
          </div>

          {committedResult.attendance && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4 animate-in fade-in-50">
              <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                <Database className="w-4 h-4 text-indigo-600" />
                <span>Attendance Write Report</span>
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200 text-center">
                  <div className="text-[10px] font-bold text-emerald-700 uppercase">Inserted</div>
                  <div className="text-lg font-extrabold text-emerald-900 mt-1">{committedResult.attendance.inserted}</div>
                </div>
                <div className="p-3 bg-blue-50 rounded-2xl border border-blue-200 text-center">
                  <div className="text-[10px] font-bold text-blue-700 uppercase">Updated / Overwritten</div>
                  <div className="text-lg font-extrabold text-blue-900 mt-1">{committedResult.attendance.updated}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 text-center">
                  <div className="text-[10px] font-bold text-slate-500 uppercase">Excluded (Flagged)</div>
                  <div className="text-lg font-extrabold text-slate-900 mt-1">{committedResult.attendance.excluded_events}</div>
                </div>
                <div className="p-3 bg-rose-50 rounded-2xl border border-rose-200 text-center">
                  <div className="text-[10px] font-bold text-rose-700 uppercase">Below 75% Threshold</div>
                  <div className="text-lg font-extrabold text-rose-900 mt-1">{committedResult.attendance.below_threshold_count}</div>
                </div>
              </div>

              {committedResult.attendance.below_threshold.length > 0 && (
                <div className="p-4 bg-rose-50/60 rounded-2xl border border-rose-200 space-y-2">
                  <div className="font-bold text-rose-900 text-[11px]">Students below attendance threshold (highlighted in the export)</div>
                  <ul className="space-y-1 max-h-40 overflow-y-auto">
                    {committedResult.attendance.below_threshold.map((row, idx) => (
                      <li key={idx} className="text-[11px] text-rose-800 font-medium">
                        {String(row.roll_no ?? row.student_id ?? '-')} — {String(row.name ?? '-')} — {String(row.percentage ?? '-')}%
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={handleExport}
                  disabled={exporting}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs shadow-md shadow-indigo-600/30 transition-all flex items-center space-x-2 disabled:opacity-60 cursor-pointer"
                >
                  <FileText className="w-4 h-4" />
                  <span>{exporting ? 'Preparing Export...' : 'Download Updated Attendance Sheet'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

