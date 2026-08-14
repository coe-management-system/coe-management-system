'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Department } from '@/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { Building2, Users, GraduationCap } from 'lucide-react';

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDepartments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDepartments();
      setDepartments(data);
    } catch (err) {
      console.error('Failed to load departments', err);
      const msg = err instanceof Error ? err.message : 'Unable to load department directory. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Departments Directory"
        subtitle="Institutional Academic Departments, Codes & Program Descriptions"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Departments' }]}
        action={
          <div className="flex items-center space-x-2 bg-indigo-50 px-3 py-1.5 rounded-xl border border-indigo-100 text-xs text-indigo-700 font-semibold">
            <Building2 className="w-4 h-4 text-indigo-600" />
            <span>{departments.length} Active Departments</span>
          </div>
        }
      />

      {loading && <LoadingState message="Loading department directory..." />}

      {!loading && error && <ErrorState message={error} onRetry={fetchDepartments} />}

      {!loading && !error && departments.length === 0 && (
        <EmptyState
          title="No departments found."
          message="No active institutional departments are registered in the database."
        />
      )}

      {!loading && !error && departments.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Department Name</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Head of Department</th>
                  <th className="py-3 px-4 text-center">Students</th>
                  <th className="py-3 px-4 text-center">Faculty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {departments.map((dept) => (
                  <tr key={dept.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-indigo-600">
                      <span className="inline-block px-2 py-0.5 rounded bg-indigo-50 border border-indigo-100">
                        {dept.code}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {dept.name}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 max-w-md">
                      {dept.description}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-800">
                      {dept.head || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-center font-semibold text-slate-700">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                        <Users className="w-3 h-3 text-slate-500" />
                        <span>{dept.studentCount || 0}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center font-semibold text-slate-700">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                        <GraduationCap className="w-3 h-3 text-slate-500" />
                        <span>{dept.facultyCount || 0}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {departments.length} academic departments</span>
            <span>Institutional Department Directory</span>
          </div>
        </div>
      )}
    </div>
  );
}
