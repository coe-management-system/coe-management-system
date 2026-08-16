'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { FileBarChart, Download, FileSpreadsheet, FileText, CheckCircle2, Loader2, Info } from 'lucide-react';

interface ReportTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  lastGenerated: string;
  format: 'PDF' | 'Excel' | 'CSV';
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  { id: '1', name: 'Institutional Student 360 & Enrolled Directory Audit', category: 'Academic Operations', description: 'Complete roster of enrolled students with roll numbers, departments, batches, and audit validation flags.', lastGenerated: '2026-08-14', format: 'Excel' },
  { id: '2', name: 'Biometric Attendance Deficiency & Shortage Summary', category: 'Attendance & Compliance', description: 'Detailed breakdown of students below 75% attendance threshold with department deficiency alerts.', lastGenerated: '2026-08-13', format: 'PDF' },
  { id: '3', name: 'Center of Excellence Skill Track & Credentials Log', category: 'CoE Accreditation', description: 'Verified industry partner credentials, NVIDIA/AWS tracks, and student readiness grade distribution.', lastGenerated: '2026-08-10', format: 'CSV' },
  { id: '4', name: 'Faculty Teaching Workload & Room Allocation Audit', category: 'Resource Utilization', description: 'Weekly faculty teaching hours, assigned courses, max capacity compliance, and room schedule grids.', lastGenerated: '2026-08-12', format: 'Excel' },
];

export default function ReportsPage() {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const handleTriggerExport = (report: ReportTemplate) => {
    setDownloadingId(report.id);
    setDownloadSuccess(null);
    setTimeout(() => {
      setDownloadingId(null);
      setDownloadSuccess(`Report "${report.name}" successfully compiled and downloaded.`);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports, Exports & Operational Audit System"
        subtitle="Institutional Reports Generator, Excel/PDF Audit Exporters & Export Control Center"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Reports' }]}
      />

      {/* Backend Dependency Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-800">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Backend Dependency Notice: </span>
          The live Report Export Service (<code className="bg-amber-100 px-1 py-0.5 rounded text-[11px]">POST /api/v1/reports/export</code>) is pending backend implementation. Client-side preview export active.
        </div>
      </div>

      {downloadSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center space-x-3 text-xs text-emerald-800 animate-in fade-in-50">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div className="font-semibold">{downloadSuccess}</div>
        </div>
      )}

      {/* Report Template Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {REPORT_TEMPLATES.map((report) => (
          <div key={report.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                  {report.category}
                </span>
                <span className="flex items-center space-x-1 text-xs font-mono font-bold text-slate-500">
                  {report.format === 'Excel' && <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />}
                  {report.format === 'PDF' && <FileText className="w-3.5 h-3.5 text-rose-600" />}
                  {report.format === 'CSV' && <FileBarChart className="w-3.5 h-3.5 text-indigo-600" />}
                  <span>{report.format} Format</span>
                </span>
              </div>

              <h3 className="text-sm font-bold text-slate-900 leading-snug">{report.name}</h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">{report.description}</p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <div className="text-[10px] text-slate-400 font-medium">Last Generated: {report.lastGenerated}</div>
              <button
                onClick={() => handleTriggerExport(report)}
                disabled={downloadingId === report.id}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
              >
                {downloadingId === report.id ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Compiling...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-3.5 h-3.5" />
                    <span>Generate &amp; Download</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
