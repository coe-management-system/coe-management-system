'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Student } from '@/types/student';
import { PageHeader } from '@/components/ui/PageHeader';
import { StudentFilters } from '@/components/students/StudentFilters';
import { StudentTable } from '@/components/students/StudentTable';
import { CreateStudentModal } from '@/components/students/CreateStudentModal';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Users, GraduationCap, Building2, UserCheck, UserPlus, ChevronLeft, ChevronRight } from 'lucide-react';

const ITEMS_PER_PAGE = 10;


export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [department, setDepartment] = useState('All');
  const [batch, setBatch] = useState('All');
  const [group, setGroup] = useState('All');

  // Client-side Pagination State (Backend contract returns complete list)
  const [currentPage, setCurrentPage] = useState(1);

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

  // Reset to Page 1 whenever search query or filters change
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  const handleDepartmentChange = (dept: string) => {
    setDepartment(dept);
    setCurrentPage(1);
  };

  const handleBatchChange = (b: string) => {
    setBatch(b);
    setCurrentPage(1);
  };

  const handleGroupChange = (g: string) => {
    setGroup(g);
    setCurrentPage(1);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setDepartment('All');
    setBatch('All');
    setGroup('All');
    setCurrentPage(1);
  };

  const handleStudentCreated = (newStudent: Student) => {
    setStudents((prev) => [newStudent, ...prev]);

    setCurrentPage(1);
  };

  // Client-side pagination calculations
  const totalStudents = students.length;
  const totalPages = Math.max(1, Math.ceil(totalStudents / ITEMS_PER_PAGE));
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, totalStudents);
  const paginatedStudents = students.slice(startIndex, endIndex);


  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Management & 360 Inventory"
        subtitle="Institutional Directory, Academic Progress & CoE Credentials Tracking"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Students' }]}
        action={
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/30 transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <UserPlus className="w-4 h-4" />
              <span>Register New Student</span>
            </button>
            <div className="hidden sm:flex items-center space-x-2 bg-indigo-50 px-3 py-2 rounded-xl border border-indigo-100 text-xs text-indigo-700 font-semibold">
              <Users className="w-4 h-4 text-indigo-600" />
              <span>{totalStudents} Enrolled Total</span>

            </div>
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
            <div className="text-xl font-bold text-slate-900">{totalStudents} Records</div>
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
        onSearchChange={handleSearchChange}
        onDepartmentChange={handleDepartmentChange}
        onBatchChange={handleBatchChange}
        onGroupChange={handleGroupChange}
        onResetFilters={handleResetFilters}
      />

      {/* Loading State */}
      {loading && <LoadingState message="Loading students..." />}

      {/* Error State */}
      {!loading && error && <ErrorState message={error} onRetry={fetchStudents} />}

      {/* Table & Pagination */}
      {!loading && !error && (
        <div className="space-y-4">
          <StudentTable students={paginatedStudents} />

          {/* Client-side Pagination Toolbar */}
          {totalStudents > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-2xs text-xs">
              <div className="text-slate-500 font-medium">
                Showing <span className="font-bold text-slate-900">{startIndex + 1}</span> to{' '}
                <span className="font-bold text-slate-900">{endIndex}</span> of{' '}
                <span className="font-bold text-slate-900">{totalStudents}</span> student records
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-slate-600 font-semibold">
                  Page {currentPage} of {totalPages}
                </span>

                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Previous Page"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Next Page"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Student Creation Modal */}
      <CreateStudentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onStudentCreated={handleStudentCreated}
      />
    </div>
  );
}
