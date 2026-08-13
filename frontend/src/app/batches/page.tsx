'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Batch } from '@/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { Layers, Users, Loader2 } from 'lucide-react';

export default function BatchesPage() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await api.getBatches();
        setBatches(data);
      } catch (err) {
        console.error('Failed to load batches', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Academic Batches"
        subtitle="Institutional Cohorts, Graduation Years & Associated Departments"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Batches' }]}
        action={
          <div className="flex items-center space-x-2 bg-indigo-50 px-3 py-1.5 rounded-xl border border-indigo-100 text-xs text-indigo-700 font-semibold">
            <Layers className="w-4 h-4 text-indigo-600" />
            <span>{batches.length} Active Cohorts</span>
          </div>
        }
      />

      {loading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-2xs">
          <Loader2 className="w-7 h-7 text-indigo-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-700">Loading academic batches...</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Batch Name</th>
                  <th className="py-3 px-4">Academic Year</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4 text-center">Enrolled Students</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {batches.map((batch) => (
                  <tr key={batch.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {batch.name}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-indigo-600">
                      {batch.year}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-800">
                        {batch.department}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center font-semibold text-slate-700">
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold border border-indigo-100">
                        <Users className="w-3 h-3 text-indigo-600" />
                        <span>{batch.studentCount || 0} Students</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {batches.length} active batch cohorts</span>
            <span>Institutional Batch Directory</span>
          </div>
        </div>
      )}
    </div>
  );
}
