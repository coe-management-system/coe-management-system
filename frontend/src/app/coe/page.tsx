'use client';

import React, { useEffect, useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { api } from '@/lib/api';
import { Department } from '@/types';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ShieldCheck, Building2, Users, Award, Loader2 } from 'lucide-react';

interface CoeCenter {
  id: string;
  name: string;
  partner: string;
  leadFaculty: string;
  enrolledStudents: number;
  activeProjects: number;
  placementRate: number;
  status: 'Operational' | 'Expanding' | 'Setup Phase';
}

const COE_CENTERS: CoeCenter[] = [
  { id: '1', name: 'NVIDIA AI & High-Performance Computing CoE', partner: 'NVIDIA Corporation', leadFaculty: 'Dr. V. Gupta', enrolledStudents: 145, activeProjects: 12, placementRate: 96.5, status: 'Operational' },
  { id: '2', name: 'AWS Cloud & DevOps Excellence Hub', partner: 'Amazon Web Services', leadFaculty: 'Prof. A. Kulkarni', enrolledStudents: 180, activeProjects: 15, placementRate: 94.0, status: 'Operational' },
  { id: '3', name: 'Cadence VLSI & Embedded Systems CoE', partner: 'Cadence Design Systems', leadFaculty: 'Dr. M. Roy', enrolledStudents: 90, activeProjects: 8, placementRate: 91.2, status: 'Operational' },
  { id: '4', name: 'Palo Alto Cybersecurity Threat Intelligence Lab', partner: 'Palo Alto Networks', leadFaculty: 'Dr. P. Sharma', enrolledStudents: 65, activeProjects: 5, placementRate: 88.0, status: 'Expanding' },
];

export default function CoePage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDepts = async () => {
      try {
        const data = await api.getDepartments();
        setDepartments(data);
      } catch (err) {
        console.error('Failed to load real departments for CoE view:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDepts();
  }, []);

  const totalEnrolledCoE = COE_CENTERS.reduce((acc, c) => acc + c.enrolledStudents, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Center of Excellence & Departmental Performance Overview"
        subtitle="Institutional Centers of Excellence, Industry Partner Hubs & Departmental Analytics"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Center of Excellence' }]}
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Active Centers</div>
            <div className="text-xl font-bold text-slate-900">{COE_CENTERS.length} Industry Hubs</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">CoE Enrolled Students</div>
            <div className="text-xl font-bold text-emerald-600">{totalEnrolledCoE} Students</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Avg Placement Rate</div>
            <div className="text-xl font-bold text-purple-600">92.4% Industry</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Active Departments</div>
            <div className="text-xl font-bold text-slate-900">{loading ? '...' : departments.length} Facilities</div>
          </div>
        </div>
      </div>

      {/* Centers of Excellence Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Operational Centers of Excellence</h3>
          <span className="text-[11px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-semibold">Industry Aligned</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Center of Excellence</th>
                <th className="py-3.5 px-4">Partner Entity</th>
                <th className="py-3.5 px-4">Lead Faculty</th>
                <th className="py-3.5 px-4 text-center">Enrolled</th>
                <th className="py-3.5 px-4 text-center">Placement Rate</th>
                <th className="py-3.5 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {COE_CENTERS.map((coe) => (
                <tr key={coe.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">{coe.name}</td>
                  <td className="py-3.5 px-4 text-slate-600 font-semibold">{coe.partner}</td>
                  <td className="py-3.5 px-4 text-slate-700">{coe.leadFaculty}</td>
                  <td className="py-3.5 px-4 text-center font-semibold">{coe.enrolledStudents} Trainees</td>
                  <td className="py-3.5 px-4 text-center font-bold text-emerald-600">{coe.placementRate}%</td>
                  <td className="py-3.5 px-4 text-right">
                    <StatusBadge status={coe.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Integrated Departments Grid (Consumes real backend departments) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-2xs space-y-4">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Institutional Academic Departments (Live API Data)</h3>

        {loading ? (
          <div className="py-8 text-center text-xs text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-600" />
            Loading live departments...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {departments.map((d) => (
              <div key={d.id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-indigo-600">{d.code}</span>
                  <span className="text-[10px] text-slate-400 font-semibold">ID #{d.id}</span>
                </div>
                <h4 className="text-xs font-bold text-slate-900 leading-snug">{d.name}</h4>
                <p className="text-[11px] text-slate-500">{d.description || 'Active Academic & Research Facility'}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
