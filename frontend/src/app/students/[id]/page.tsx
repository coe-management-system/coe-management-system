'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Student } from '@/types/student';
import { PageHeader } from '@/components/ui/PageHeader';
import { StudentProfileView } from '@/components/students/StudentProfileView';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { ArrowLeft } from 'lucide-react';
import { ArrowLeft, UserX, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function StudentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStudent = useCallback(async () => {
    if (!studentId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getStudentById(studentId);
      setStudent(res);
    } catch (err) {
      console.error('Error fetching student profile:', err);
      setError(`Unable to retrieve student profile for ID ${studentId}.`);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    loadStudent();
  }, [loadStudent]);

  if (loading) {
    return <LoadingState message="Loading student profile details..." />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.push('/students')}
          className="inline-flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 shadow-2xs transition-colors mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Students List</span>
        </button>
        <ErrorState message={error} onRetry={loadStudent} />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.push('/students')}
          className="inline-flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 shadow-2xs transition-colors mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Students List</span>
        </button>
        <EmptyState
          title="Student Record Not Found"
          message={`No student matching ID or Roll Number "${studentId}" was found in the institutional database.`}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${student.name} — Student Profile Details`}
        subtitle="Institutional Academic Record & Enrolled Department Information"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Students', href: '/students' },
          { label: student.name },
        ]}
        action={
          <button
            onClick={() => router.push('/students')}
            className="inline-flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 shadow-2xs transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Students List</span>
          </button>
        }
      />

      <StudentProfileView student={student} />
    </div>
  );
}