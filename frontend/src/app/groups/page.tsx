'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Group } from '@/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { FolderTree, Users } from 'lucide-react';

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getGroups();
      setGroups(data);
    } catch (err) {
      console.error('Failed to load groups', err);
      const msg = err instanceof Error ? err.message : 'Unable to load section groups. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Section Groups"
        subtitle="Institutional Class Groups, Associated Batches & Departments"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Groups' }]}
        action={
          <div className="flex items-center space-x-2 bg-indigo-50 px-3 py-1.5 rounded-xl border border-indigo-100 text-xs text-indigo-700 font-semibold">
            <FolderTree className="w-4 h-4 text-indigo-600" />
            <span>{groups.length} Active Groups</span>
          </div>
        }
      />

      {loading && <LoadingState message="Loading student section groups..." />}

      {!loading && error && <ErrorState message={error} onRetry={fetchGroups} />}

      {!loading && !error && groups.length === 0 && (
        <EmptyState
          title="No student section groups found."
          message="No active student section groups are registered in the database."
        />
      )}

      {!loading && !error && groups.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Group Name</th>
                  <th className="py-3 px-4">Batch</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4 text-center">Group Size</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {groups.map((group) => (
                  <tr key={group.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-indigo-600 font-mono">
                      <span className="inline-block px-2.5 py-0.5 rounded bg-indigo-50 border border-indigo-100">
                        {group.name}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-800">
                      {group.batch}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-800">
                        {group.department}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center font-semibold text-slate-700">
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded bg-slate-100 text-slate-800">
                        <Users className="w-3 h-3 text-slate-500" />
                        <span>{group.studentCount || 0} Students</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {groups.length} active section groups</span>
            <span>Institutional Group Directory</span>
          </div>
        </div>
      )}
    </div>
  );
}
