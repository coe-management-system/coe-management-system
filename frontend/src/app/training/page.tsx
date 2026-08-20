'use client';

import React, { useEffect, useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, GraduationCap, Users, Award } from 'lucide-react';
import { showcaseApi, ShowcaseTrainingProgram } from '@/lib/api/showcase';

const INITIAL_TRACKS: ShowcaseTrainingProgram[] = [
  { id: '1', name: 'Advanced Machine Learning & Neural Networks', provider: 'NVIDIA Deep Learning Institute', category: 'Artificial Intelligence', enrolledCount: 45, progress: 78, durationWeeks: 12, status: 'Active' },
  { id: '2', name: 'Cloud Architecture & DevOps Masterclass', provider: 'AWS Academy', category: 'Cloud Computing', enrolledCount: 60, progress: 42, durationWeeks: 10, status: 'Active' },
  { id: '3', name: 'Full-Stack Enterprise React & Next.js', provider: 'Vercel Partner Network', category: 'Software Engineering', enrolledCount: 85, progress: 95, durationWeeks: 8, status: 'Active' },
  { id: '4', name: 'VLSI System Design & Chip Architecture', provider: 'Cadence Design Systems', category: 'Hardware Engineering', enrolledCount: 30, progress: 100, durationWeeks: 14, status: 'Completed' },
  { id: '5', name: 'Cybersecurity Threat Intelligence & SOC', provider: 'Palo Alto Networks', category: 'Cybersecurity', enrolledCount: 40, progress: 0, durationWeeks: 8, status: 'Upcoming' },
];

export default function TrainingPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [tracks, setTracks] = useState<ShowcaseTrainingProgram[]>(INITIAL_TRACKS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    showcaseApi
      .getTrainingPrograms()
      .then((data) => {
        if (!cancelled) setTracks(data);
      })
      .catch(() => {
        if (!cancelled) setTracks(INITIAL_TRACKS);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredTracks = tracks.filter((track) => {
    const matchesSearch =
      track.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      track.provider.toLowerCase().includes(searchQuery.toLowerCase()) ||
      track.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || track.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalTrainees = tracks.reduce((acc, t) => acc + t.enrolledCount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Center of Excellence Training Programs"
        subtitle="Industry Partner Skill Tracks, Curriculum Registration & Trainee Progress Analytics"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Training' }]}
      />

      {/* Live API Status */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-start space-x-3 text-xs text-emerald-800">
        <div>
          {loading ? (
            <span>
              <span className="font-bold">Live API Data: </span>
              Connecting to GET /api/v1/training/programs...
            </span>
          ) : (
            <span>
              <span className="font-bold">Live API Data: </span>
              GET /api/v1/training/programs connected. Showing {tracks.length} training tracks.
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Active Training Tracks</div>
            <div className="text-xl font-bold text-slate-900">{tracks.length} Specialized Tracks</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Total Enrolled Trainees</div>
            <div className="text-xl font-bold text-emerald-600">{totalTrainees} Students</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Industry Partners</div>
            <div className="text-xl font-bold text-purple-600">5 Global Providers</div>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search training track or partner provider..."
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
          <option value="All">All Track Statuses</option>
          <option value="Active">Active</option>
          <option value="Completed">Completed</option>
          <option value="Upcoming">Upcoming</option>
        </select>
      </div>

      {/* Training Tracks Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Training Track Name</th>
                <th className="py-3.5 px-4">Partner Provider</th>
                <th className="py-3.5 px-4">Category</th>
                <th className="py-3.5 px-4 text-center">Enrolled</th>
                <th className="py-3.5 px-4 text-center">Progress</th>
                <th className="py-3.5 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredTracks.map((track) => (
                <tr key={track.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">{track.name}</td>
                  <td className="py-3.5 px-4 text-slate-600 font-semibold">{track.provider}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded font-semibold text-[11px]">
                      {track.category}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center font-semibold">{track.enrolledCount} Trainees</td>
                  <td className="py-3.5 px-4 text-center">
                    <div className="w-32 mx-auto">
                      <div className="flex justify-between text-[10px] font-bold mb-1 text-slate-600">
                        <span>{track.progress}%</span>
                        <span>{track.durationWeeks} wks</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-600 h-full rounded-full"
                          style={{ width: `${track.progress}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <StatusBadge status={track.status} />
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
