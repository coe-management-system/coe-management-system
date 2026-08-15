'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { SlidersHorizontal, AlertTriangle, CheckCircle2, RefreshCw, Info, Layers } from 'lucide-react';

interface SchedulingConflict {
  id: string;
  type: 'Room Double-Booking' | 'Faculty Overlap' | 'Capacity Exceeded';
  resource: string;
  affectedSlot: string;
  severity: 'High' | 'Medium' | 'Low';
  recommendation: string;
}

const CONFLICT_LOGS: SchedulingConflict[] = [
  { id: '1', type: 'Room Double-Booking', resource: 'Hall 101', affectedSlot: 'Mon 09:00 AM - 10:00 AM', severity: 'High', recommendation: 'Reallocate CS301 lecture to Hall 104' },
  { id: '2', type: 'Faculty Overlap', resource: 'Dr. V. Gupta', affectedSlot: 'Wed 11:30 AM - 12:30 PM', severity: 'High', recommendation: 'Reschedule Machine Learning lecture to Friday 10:15 AM' },
  { id: '3', type: 'Capacity Exceeded', resource: 'CoE AI Lab (Cap: 40)', affectedSlot: 'Mon 01:30 PM - 03:30 PM', severity: 'Medium', recommendation: 'Split 60 enrolled students into Group A and Group B batches' },
];

export default function SchedulingPage() {
  const [runningOptimizer, setRunningOptimizer] = useState(false);
  const [optimizerSuccess, setOptimizerSuccess] = useState(false);

  const handleRunOptimizer = () => {
    setRunningOptimizer(true);
    setOptimizerSuccess(false);
    setTimeout(() => {
      setRunningOptimizer(false);
      setOptimizerSuccess(true);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Intelligent Timetable Scheduling & Conflict Resolution"
        subtitle="Automated Room Allocation, Constraint Validation & Slot Conflict Engine"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Scheduling' }]}
        action={
          <button
            onClick={handleRunOptimizer}
            disabled={runningOptimizer}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/30 transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${runningOptimizer ? 'animate-spin' : ''}`} />
            <span>{runningOptimizer ? 'Optimizing Schedule...' : 'Run Automated Conflict Solver'}</span>
          </button>
        }
      />

      {/* Backend Dependency Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-800">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Backend Dependency Notice: </span>
          The live Scheduling API (<code className="bg-amber-100 px-1 py-0.5 rounded text-[11px]">GET /api/v1/scheduling</code>) is pending implementation by Member 3. Operating in client-side preview mode.
        </div>
      </div>

      {optimizerSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center space-x-3 text-xs text-emerald-800 animate-in fade-in-50">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div className="font-medium">
            Automated Conflict Resolution complete! 3 schedule constraints evaluated and optimal room reallocations calculated.
          </div>
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <SlidersHorizontal className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Active Classrooms</div>
            <div className="text-xl font-bold text-slate-900">18 Halls &amp; Labs</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Detected Conflicts</div>
            <div className="text-xl font-bold text-amber-600">{CONFLICT_LOGS.length} Active Triggers</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Room Utilization Score</div>
            <div className="text-xl font-bold text-emerald-600">89.4% Efficiency</div>
          </div>
        </div>
      </div>

      {/* Conflict Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Detected Schedule Conflicts &amp; AI Recommendations</h3>
          <span className="text-[11px] text-slate-500 font-medium">Constraint Solver Engine v1.4</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Conflict Type</th>
                <th className="py-3.5 px-4">Target Resource</th>
                <th className="py-3.5 px-4">Affected Time Slot</th>
                <th className="py-3.5 px-4 text-center">Severity</th>
                <th className="py-3.5 px-4">Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {CONFLICT_LOGS.map((conflict) => (
                <tr key={conflict.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">{conflict.type}</td>
                  <td className="py-3.5 px-4 text-indigo-700 font-mono font-semibold">{conflict.resource}</td>
                  <td className="py-3.5 px-4 text-slate-600 font-medium">{conflict.affectedSlot}</td>
                  <td className="py-3.5 px-4 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        conflict.severity === 'High'
                          ? 'bg-rose-50 text-rose-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {conflict.severity}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-700 font-medium bg-indigo-50/30">
                    {conflict.recommendation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
