'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, Filter, AlertTriangle, CalendarCheck, CheckCircle2, Info } from 'lucide-react';

interface AttendanceRecord {
  id: string;
  studentName: string;
  rollNo: string;
  department: string;
  batch: string;
  totalClasses: number;
  attended: number;
  percentage: number;
  status: 'Sufficient' | 'Deficient' | 'Critical';
}

const INITIAL_ATTENDANCE: AttendanceRecord[] = [
  { id: '1', studentName: 'Aarav Sharma', rollNo: '2026-CSE-001', department: 'Computer Science', batch: '2022-2026', totalClasses: 120, attended: 110, percentage: 91.6, status: 'Sufficient' },
  { id: '2', studentName: 'Ananya Verma', rollNo: '2026-CSE-002', department: 'Computer Science', batch: '2022-2026', totalClasses: 120, attended: 82, percentage: 68.3, status: 'Deficient' },
  { id: '3', studentName: 'Rohan Gupta', rollNo: '2026-ECE-005', department: 'Electronics & Comm.', batch: '2022-2026', totalClasses: 115, attended: 104, percentage: 90.4, status: 'Sufficient' },
  { id: '4', studentName: 'Priya Nair', rollNo: '2026-ME-012', department: 'Mechanical Eng.', batch: '2022-2026', totalClasses: 110, attended: 70, percentage: 63.6, status: 'Critical' },
  { id: '5', studentName: 'Vikram Singh', rollNo: '2026-EE-008', department: 'Electrical Eng.', batch: '2022-2026', totalClasses: 118, attended: 98, percentage: 83.0, status: 'Sufficient' },
  { id: '6', studentName: 'Sneha Patel', rollNo: '2026-CSE-019', department: 'Computer Science', batch: '2022-2026', totalClasses: 120, attended: 74, percentage: 61.6, status: 'Critical' },
];

export default function AttendancePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  const filteredAttendance = INITIAL_ATTENDANCE.filter((item) => {
    const matchesSearch =
      item.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.rollNo.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDept = departmentFilter === 'All' || item.department === departmentFilter;
    const matchesStatus = statusFilter === 'All' || item.status === statusFilter;
    return matchesSearch && matchesDept && matchesStatus;
  });

  const totalStudents = INITIAL_ATTENDANCE.length;
  const deficientCount = INITIAL_ATTENDANCE.filter((i) => i.status !== 'Sufficient').length;
  const avgAttendance = (
    INITIAL_ATTENDANCE.reduce((acc, curr) => acc + curr.percentage, 0) / totalStudents
  ).toFixed(1);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance & Deficiency Analytics"
        subtitle="Classroom Biometric Logs, Shortage Triggers & Academic Retention Tracking"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Attendance' }]}
      />

      {/* Backend Dependency Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-800">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Backend Dependency Notice: </span>
          The live Attendance API (<code className="bg-amber-100 px-1 py-0.5 rounded text-[11px]">GET /api/v1/attendance</code>) is pending implementation by Member 1. Operating in client-side preview mode.
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <CalendarCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Avg Attendance Rate</div>
            <div className="text-xl font-bold text-slate-900">{avgAttendance}%</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Deficient Students (&lt;75%)</div>
            <div className="text-xl font-bold text-rose-600">{deficientCount} Students</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Sufficient Attendance</div>
            <div className="text-xl font-bold text-emerald-600">{totalStudents - deficientCount} Students</div>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3 shadow-2xs">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search student or roll number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600"
            />
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <div className="flex items-center space-x-1.5 text-xs text-slate-500">
              <Filter className="w-3.5 h-3.5" />
              <span>Filter:</span>
            </div>

            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600"
            >
              <option value="All">All Departments</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Electronics & Comm.">Electronics & Comm.</option>
              <option value="Mechanical Eng.">Mechanical Eng.</option>
              <option value="Electrical Eng.">Electrical Eng.</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600"
            >
              <option value="All">All Statuses</option>
              <option value="Sufficient">Sufficient (&ge;75%)</option>
              <option value="Deficient">Deficient (65-74%)</option>
              <option value="Critical">Critical (&lt;65%)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Attendance Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Student</th>
                <th className="py-3.5 px-4">Roll Number</th>
                <th className="py-3.5 px-4">Department</th>
                <th className="py-3.5 px-4">Batch</th>
                <th className="py-3.5 px-4 text-center">Attended / Total</th>
                <th className="py-3.5 px-4 text-center">Percentage</th>
                <th className="py-3.5 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredAttendance.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-900">{item.studentName}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-500">{item.rollNo}</td>
                  <td className="py-3.5 px-4 text-slate-600">{item.department}</td>
                  <td className="py-3.5 px-4 text-slate-600">{item.batch}</td>
                  <td className="py-3.5 px-4 text-center font-medium">
                    {item.attended} / {item.totalClasses}
                  </td>
                  <td className="py-3.5 px-4 text-center font-bold">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] ${
                        item.percentage >= 75
                          ? 'bg-emerald-50 text-emerald-700'
                          : item.percentage >= 65
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-rose-50 text-rose-700'
                      }`}
                    >
                      {item.percentage}%
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <StatusBadge status={item.status} />
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
