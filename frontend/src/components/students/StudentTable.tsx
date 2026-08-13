import React from 'react';
import Link from 'next/link';
import { Student } from '@/types/student';
import { Eye, Award, AlertTriangle } from 'lucide-react';

interface StudentTableProps {
  students: Student[];
}

export const StudentTable: React.FC<StudentTableProps> = ({ students }) => {
  if (students.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
        <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-3">
          <AlertTriangle className="w-6 h-6 text-slate-400" />
        </div>
        <h3 className="text-sm font-bold text-slate-800">No students found.</h3>
        <p className="text-xs text-slate-500 mt-1">
          Try adjusting your search criteria or resetting filters.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-4">Roll Number</th>
              <th className="py-3 px-4">Student Name</th>
              <th className="py-3 px-4">Email</th>
              <th className="py-3 px-4">Department</th>
              <th className="py-3 px-4">Batch</th>
              <th className="py-3 px-4">Group</th>
              <th className="py-3 px-4">Attendance</th>
              <th className="py-3 px-4">Credentials</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {students.map((student) => {
              const roll = student.roll_no || student.rollNumber || '';
              const attPct = student.attendancePercentage ?? 88;
              const certs = student.certifications || [];

              return (
                <tr key={student.id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="py-3.5 px-4 font-mono font-semibold text-indigo-600">
                    {roll}
                  </td>
                  <td className="py-3.5 px-4 font-bold text-slate-900">
                    <Link
                      href={`/students/${student.id}`}
                      className="hover:text-indigo-600 transition-colors"
                    >
                      {student.name}
                    </Link>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono text-[11px]">
                    {student.email}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-800">
                      {student.department}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600">{student.batch}</td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700">
                      {student.group}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-12 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            attPct >= 90
                              ? 'bg-emerald-500'
                              : attPct >= 80
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${attPct}%` }}
                        />
                      </div>
                      <span className="font-semibold text-slate-800">
                        {attPct}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    {certs.length > 0 ? (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                        <Award className="w-3 h-3" />
                        <span>{certs.length} Credentials</span>
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[11px]">None Yet</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      href={`/students/${student.id}`}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-600 hover:text-white rounded-lg font-semibold text-xs transition-all shadow-2xs"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View Profile</span>
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-3 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
        <span>Showing {students.length} student records</span>
        <span>Institutional Student Inventory</span>
      </div>
    </div>
  );
};
