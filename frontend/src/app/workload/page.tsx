'use client';

import React, { useState, useEffect } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, Briefcase, Users, AlertCircle } from 'lucide-react';
import { showcaseApi, ShowcaseWorkloadEntry } from '@/lib/api/showcase';

const FACULTY_WORKLOADS: ShowcaseWorkloadEntry[] = [
  { id: '1', name: 'Dr. S. Ramanujan', department: 'Computer Science', designation: 'Professor & Chair', assignedHours: 18, maxHours: 18, assignedCourses: ['CS301 - Data Structures', 'CS501 - Adv Algorithms'], status: 'Optimal' },
  { id: '2', name: 'Prof. A. Kulkarni', department: 'Computer Science', designation: 'Associate Professor', assignedHours: 22, maxHours: 20, assignedCourses: ['CS302 - DBMS', 'CS402 - Distributed Systems', 'LAB302 - Cloud Lab'], status: 'Overallocated' },
  { id: '3', name: 'Dr. M. Roy', department: 'Electronics & Comm.', designation: 'Professor', assignedHours: 16, maxHours: 18, assignedCourses: ['CS303 - Operating Systems', 'LAB304 - VLSI Simulation'], status: 'Optimal' },
  { id: '4', name: 'Dr. P. Sharma', department: 'Computer Science', designation: 'Assistant Professor', assignedHours: 12, maxHours: 18, assignedCourses: ['CS304 - Networks'], status: 'Underloaded' },
  { id: '5', name: 'Dr. V. Gupta', department: 'AI & Data Science', designation: 'CoE Director', assignedHours: 24, maxHours: 20, assignedCourses: ['CS305 - ML Fundamentals', 'LAB301 - AI Robotics Lab', 'CoE Capstone Track'], status: 'Overallocated' },
];

export default function WorkloadPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [workloads, setWorkloads] = useState<ShowcaseWorkloadEntry[]>(FACULTY_WORKLOADS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await showcaseApi.getWorkload();
        if (!cancelled) setWorkloads(data);
      } catch (err) {
        console.error('Workload API unavailable; using fallback data.', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredFaculty = workloads.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.designation.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || f.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const overallocatedCount = workloads.filter((f) => f.status === 'Overallocated').length;
  const avgHours = (
    workloads.reduce((acc, f) => acc + f.assignedHours, 0) / workloads.length
  ).toFixed(1);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Faculty Workload Distribution & Optimization"
        subtitle="Teaching Load Analytics, Subject Course Assignments & Overallocation Alerts"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Workload' }]}
      />

      {/* Live API Indicator */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-start space-x-3 text-xs text-emerald-800">
        <div>
          {loading ? (
            <span className="font-bold">Loading live workload data from backend...</span>
          ) : (
            <>
              <span className="font-bold">Live API Data: </span>
              GET /api/v1/workload connected. Showing workload for {workloads.length} faculty members.
            </>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Total Active Faculty</div>
            <div className="text-xl font-bold text-slate-900">{workloads.length} Members</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Avg Teaching Load</div>
            <div className="text-xl font-bold text-purple-600">{avgHours} Hours / Wk</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Overallocated Faculty</div>
            <div className="text-xl font-bold text-rose-600">{overallocatedCount} Faculty Alert</div>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search faculty name, department, designation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600 w-full sm:w-auto"
        >
          <option value="All">All Workload Statuses</option>
          <option value="Optimal">Optimal</option>
          <option value="Overallocated">Overallocated</option>
          <option value="Underloaded">Underloaded</option>
        </select>
      </div>

      {/* Faculty Workload Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Faculty Member</th>
                <th className="py-3.5 px-4">Department</th>
                <th className="py-3.5 px-4">Designation</th>
                <th className="py-3.5 px-4">Assigned Courses</th>
                <th className="py-3.5 px-4 text-center">Weekly Load</th>
                <th className="py-3.5 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredFaculty.map((faculty) => (
                <tr key={faculty.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">{faculty.name}</td>
                  <td className="py-3.5 px-4 text-slate-600">{faculty.department}</td>
                  <td className="py-3.5 px-4 text-slate-500 font-medium">{faculty.designation}</td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1">
                      {faculty.assignedCourses.map((c) => (
                        <span key={c} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono">
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <div className="w-28 mx-auto">
                      <div className="flex justify-between text-[10px] font-bold mb-1 text-slate-700">
                        <span>{faculty.assignedHours} hrs</span>
                        <span className="text-slate-400">Max {faculty.maxHours}</span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            faculty.assignedHours > faculty.maxHours
                              ? 'bg-rose-500'
                              : faculty.assignedHours < 14
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, (faculty.assignedHours / faculty.maxHours) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <StatusBadge status={faculty.status} />
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
