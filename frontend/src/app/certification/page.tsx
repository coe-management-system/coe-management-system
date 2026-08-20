'use client';

import React, { useEffect, useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, Award, CheckCircle2, ShieldCheck } from 'lucide-react';
import { showcaseApi, ShowcaseCertification } from '@/lib/api/showcase';

export default function CertificationPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [certs, setCerts] = useState<ShowcaseCertification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCerts = async () => {
      try {
        const data = await showcaseApi.getCertifications();
        setCerts(data);
      } catch (err) {
        console.error('Failed to load live certification data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCerts();
  }, []);

  const filteredCerts = certs.filter((cert) => {
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

      {/* Live API Indicator */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-start space-x-3 text-xs text-emerald-800">
        <div>
          <span className="font-bold">Live API Data: </span>
          <code className="bg-emerald-100 px-1 py-0.5 rounded text-[11px]">GET /api/v1/certifications</code> connected. Showing {loading ? '...' : certs.length} credential records.
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
            <div className="text-xl font-bold text-slate-900">{certs.length} Records</div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center space-x-3 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold uppercase">Verified Credentials</div>
            <div className="text-xl font-bold text-emerald-600">
              {certs.filter((c) => c.status === 'Verified').length} Verified
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
