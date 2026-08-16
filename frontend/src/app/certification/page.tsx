'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, Award, CheckCircle2, ShieldCheck, Info } from 'lucide-react';

interface CertificationRecord {
  id: string;
  name: string;
  studentName: string;
  rollNo: string;
  issuingBody: string;
  credentialId: string;
  issueDate: string;
  status: 'Verified' | 'Pending' | 'Audit Flagged';
}

const INITIAL_CERTS: CertificationRecord[] = [
  { id: '1', name: 'AWS Certified Solutions Architect – Associate', studentName: 'Aarav Sharma', rollNo: '2026-CSE-001', issuingBody: 'Amazon Web Services', credentialId: 'AWS-ASA-2026-891', issueDate: '2026-01-15', status: 'Verified' },
  { id: '2', name: 'NVIDIA Certified Associate – Generative AI', studentName: 'Rohan Gupta', rollNo: '2026-ECE-005', issuingBody: 'NVIDIA Academy', credentialId: 'NV-AI-7712-09', issueDate: '2026-02-10', status: 'Verified' },
  { id: '3', name: 'Cadence Certified VLSI Design Specialist', studentName: 'Priya Nair', rollNo: '2026-ME-012', issuingBody: 'Cadence Design Systems', credentialId: 'CAD-VLSI-4421', issueDate: '2025-11-20', status: 'Verified' },
  { id: '4', name: 'TensorFlow Developer Certificate', studentName: 'Vikram Singh', rollNo: '2026-EE-008', issuingBody: 'Google Developers', credentialId: 'TF-DEV-9901', issueDate: '2026-03-01', status: 'Pending' },
];

export default function CertificationPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  const filteredCerts = INITIAL_CERTS.filter((cert) => {
    const matchesSearch =
      cert.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cert.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cert.rollNo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cert.issuingBody.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || cert.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Verified Industry Credentials & Certifications"
        subtitle="Center of Excellence Student Credentials Verification & Audit Repository"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Certification' }]}
      />

      {/* Backend Dependency Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-800">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Backend Dependency Notice: </span>
          The live Certification API (<code className="bg-amber-100 px-1 py-0.5 rounded text-[11px]">GET /api/v1/certification</code>) is pending backend implementation. Operating in client-side preview mode.
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Total Issued Credentials</div>
            <div className="text-xl font-bold text-slate-900">{INITIAL_CERTS.length} Records</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Verified Credentials</div>
            <div className="text-xl font-bold text-emerald-600">
              {INITIAL_CERTS.filter((c) => c.status === 'Verified').length} Verified
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Audit Integrity Score</div>
            <div className="text-xl font-bold text-indigo-600">100% Validated</div>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search credential, student, or issuing body..."
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
          <option value="All">All Verification Statuses</option>
          <option value="Verified">Verified</option>
          <option value="Pending">Pending</option>
        </select>
      </div>

      {/* Certifications Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Credential Name</th>
                <th className="py-3.5 px-4">Student</th>
                <th className="py-3.5 px-4">Roll Number</th>
                <th className="py-3.5 px-4">Issuing Body</th>
                <th className="py-3.5 px-4">Credential ID</th>
                <th className="py-3.5 px-4">Issue Date</th>
                <th className="py-3.5 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredCerts.map((cert) => (
                <tr key={cert.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">{cert.name}</td>
                  <td className="py-3.5 px-4 font-semibold text-slate-800">{cert.studentName}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-500">{cert.rollNo}</td>
                  <td className="py-3.5 px-4 text-slate-600">{cert.issuingBody}</td>
                  <td className="py-3.5 px-4 font-mono text-xs text-indigo-600">{cert.credentialId}</td>
                  <td className="py-3.5 px-4 text-slate-500">{cert.issueDate}</td>
                  <td className="py-3.5 px-4 text-right">
                    <StatusBadge status={cert.status} />
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
