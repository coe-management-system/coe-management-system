'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Student } from '@/types/student';
import { PageHeader } from '@/components/ui/PageHeader';
import { StudentFilters } from '@/components/students/StudentFilters';
import { StudentTable } from '@/components/students/StudentTable';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Users, GraduationCap, Building2, UserCheck } from 'lucide-react';

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [department, setDepartment] = useState('All');
  const [batch, setBatch] = useState('All');
  const [group, setGroup] = useState('All');

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStudents({
        searchQuery,
        department,
        batch,
        group,
      });
      setStudents(data);
    } catch (err) {
      console.error('Failed to fetch students', err);
      const msg = err instanceof Error ? err.message : 'Unable to load students. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, department, batch, group]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setDepartment('All');
    setBatch('All');
    setGroup('All');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Management & 360 Inventory"
        subtitle="Institutional Directory, Academic Progress & CoE Credentials Tracking"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Students' }]}
        action={
          <div className="flex items-center space-x-2 bg-indigo-50 px-3 py-1.5 rounded-xl border border-indigo-100 text-xs text-indigo-700 font-semibold">
            <Users className="w-4 h-4 text-indigo-600" />
            <span>{students.length} Enrolled Total</span>
          </div>
        }
      />

      {/* Summary Counters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Total Active Directory</div>
            <div className="text-xl font-bold text-slate-900">{students.length} Records</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Active Batches</div>
            <div className="text-xl font-bold text-slate-900">Academic Cohorts</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Departments</div>
            <div className="text-xl font-bold text-slate-900">Active Facilities</div>
          </div>
        </div>
      </div>

      {/* Real-time Search & Combined Filters */}
      <StudentFilters
        searchQuery={searchQuery}
        department={department}
        batch={batch}
        group={group}
        onSearchChange={setSearchQuery}
        onDepartmentChange={setDepartment}
        onBatchChange={setBatch}
        onGroupChange={setGroup}
        onResetFilters={handleResetFilters}
      />

      {/* Loading State */}
      {loading && <LoadingState message="Loading students..." />}

      {/* Error State */}
      {!loading && error && <ErrorState message={error} onRetry={fetchStudents} />}

      {/* Table & Empty State */}
      {!loading && !error && (
        <StudentTable students={students} />
      )}
    </div>
  );
}