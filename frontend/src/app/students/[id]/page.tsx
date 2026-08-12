'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Student } from '@/types/student';
import { PageHeader } from '@/components/ui/PageHeader';
import { StudentProfileView } from '@/components/students/StudentProfileView';
import { ArrowLeft, UserX, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function StudentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStudent() {
      setLoading(true);
      try {
        const res = await api.getStudentById(studentId);
        setStudent(res);
      } catch (err) {
        console.error('Error fetching student profile:', err);
      } finally {
        setLoading(false);
      }
    }

    if (studentId) {
      loadStudent();
    }
  }, [studentId]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-2">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        <p className="text-xs font-semibold text-slate-500">Loading Student 360 Profile...</p>
      </div>
    );
  }

  // Graceful Not-Found State for invalid or non-existent student IDs
  if (!student) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center">
        <div className="w-16 h-16 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-rose-100">
          <UserX className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Student Profile Not Found</h2>
        <p className="text-xs text-slate-600 mb-6">
          No student matching ID or Roll Number <code className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-rose-600">{studentId}</code> was found in the institutional database.
        </p>
        <Link
          href="/students"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 transition-colors shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Student Directory</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${student.name} — Student 360 Operational View`}
        subtitle="Comprehensive Academic Performance, CoE Certifications & Industry Readiness Matrix"
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
            <span>Back to Directory</span>
          </button>
        }
      />

      <StudentProfileView student={student} />
    </div>
  );
}
