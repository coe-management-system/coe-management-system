'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Settings, Shield, Bell, CheckCircle2, Save } from 'lucide-react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'notifications'>('general');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Configuration & Operational Policies"
        subtitle="Global Platform Settings, Security Roles, Attendance Deficiency Thresholds & Academic Term Parameters"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Settings' }]}
      />

      {savedSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center space-x-3 text-xs text-emerald-800 animate-in fade-in-50">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div className="font-semibold">System settings successfully saved and applied to active session.</div>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-2 flex items-center space-x-2 shadow-2xs w-fit">
        <button
          onClick={() => setActiveTab('general')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
            activeTab === 'general' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Settings className="w-3.5 h-3.5" />
          <span>General Parameters</span>
        </button>

        <button
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
            activeTab === 'security' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Shield className="w-3.5 h-3.5" />
          <span>Security &amp; Roles</span>
        </button>

        <button
          onClick={() => setActiveTab('notifications')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
            activeTab === 'notifications' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Bell className="w-3.5 h-3.5" />
          <span>Automated Triggers</span>
        </button>
      </div>

      {/* Settings Form Container */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs max-w-3xl">
        <form onSubmit={handleSaveSettings} className="space-y-6">
          {activeTab === 'general' && (
            <div className="space-y-4 text-xs">
              <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Academic Term Parameters</h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Active Academic Term</label>
                  <input
                    type="text"
                    defaultValue="Spring Semester 2026"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Attendance Shortage Threshold (%)</label>
                  <input
                    type="number"
                    defaultValue={75}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase mb-1">Institution Name</label>
                <input
                  type="text"
                  defaultValue="National Institute of Technology & Center of Excellence"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-4 text-xs">
              <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Role Access Control Policies</h3>

              <div className="space-y-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900">Administrator Role</div>
                    <div className="text-slate-500 text-[11px]">Full access to student CRUD, Excel ingestion, and scheduling triggers</div>
                  </div>
                  <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded font-bold">Enabled</span>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-900">Faculty Role</div>
                    <div className="text-slate-500 text-[11px]">Access to view student profile, attendance logs, and workload summary</div>
                  </div>
                  <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded font-bold">Enabled</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-4 text-xs">
              <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Automated Alert Triggers</h3>

              <div className="space-y-2">
                <label className="flex items-center space-x-2 text-slate-800 font-medium">
                  <input type="checkbox" defaultChecked className="rounded text-indigo-600 focus:ring-indigo-600" />
                  <span>Send automated deficiency alert email when attendance drops below 75%</span>
                </label>

                <label className="flex items-center space-x-2 text-slate-800 font-medium">
                  <input type="checkbox" defaultChecked className="rounded text-indigo-600 focus:ring-indigo-600" />
                  <span>Notify Department Chair upon faculty teaching workload overallocation (&gt;20 hrs)</span>
                </label>

                <label className="flex items-center space-x-2 text-slate-800 font-medium">
                  <input type="checkbox" defaultChecked className="rounded text-indigo-600 focus:ring-indigo-600" />
                  <span>Trigger instant notification upon successful Excel student batch import</span>
                </label>
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
            <button
              type="submit"
              className="px-5 py-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/30 transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <Save className="w-4 h-4" />
              <span>Save System Settings</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
