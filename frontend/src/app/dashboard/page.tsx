'use client';

import React, { useEffect, useState } from 'react';
import { dashboardApi } from '@/lib/api/dashboard';
import { DashboardData } from '@/types/dashboard';
import { PageHeader } from '@/components/ui/PageHeader';
import { KpiGrid } from '@/components/dashboard/KpiGrid';
import { DepartmentAttendanceChart } from '@/components/charts/DepartmentAttendanceChart';
import { MonthlyTrendChart } from '@/components/charts/MonthlyTrendChart';
import { CertificationTrainingChart } from '@/components/charts/CertificationTrainingChart';
import { FacultyWorkloadChart } from '@/components/charts/FacultyWorkloadChart';
import { AlertCenter } from '@/components/dashboard/AlertCenter';
import { CoeSummary } from '@/components/dashboard/CoeSummary';
import { ErrorState } from '@/components/ui/ErrorState';
import { RefreshCw, Download } from 'lucide-react';
import {
  MOCK_KPIS,
  MOCK_COE_SUMMARIES,
  MOCK_ATTENDANCE_COMPARISON,
  MOCK_MONTHLY_TREND,
  MOCK_TRAINING_CERT_DATA,
  MOCK_WORKLOAD_DATA,
} from '@/lib/mock-data/dashboard';
import { MOCK_ALERTS } from '@/lib/mock-data/alerts';

const INITIAL_DASHBOARD_DATA: DashboardData = {
  kpis: MOCK_KPIS,
  alerts: MOCK_ALERTS,
  coeSummaries: MOCK_COE_SUMMARIES,
  attendanceComparison: MOCK_ATTENDANCE_COMPARISON,
  monthlyTrend: MOCK_MONTHLY_TREND,
  trainingCertData: MOCK_TRAINING_CERT_DATA,
  workloadData: MOCK_WORKLOAD_DATA,
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>(INITIAL_DASHBOARD_DATA);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const res = await dashboardApi.getDashboardData();
      setData(res);
    } catch (err) {
      console.error('Failed to load dashboard metrics', err);
      setError('Unable to fetch live dashboard metrics. Displaying cached operational data.');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return (
    <div className="space-y-6">
      {/* Dashboard Top Header & Action Controls */}
      <PageHeader
        title="Academic & Center of Excellence Operational Dashboard"
        subtitle="Institutional Decision Support System & Resource Optimization Analytics"
        breadcrumbs={[{ label: 'Home' }, { label: 'Operational Dashboard' }]}
        action={
          <>
            <button
              onClick={fetchDashboard}
              disabled={refreshing}
              className="inline-flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 shadow-2xs transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh Metrics</span>
            </button>
            <button
              onClick={() => alert('Operational Audit Report PDF export triggered (Mock).')}
              className="inline-flex items-center space-x-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Audit Summary</span>
            </button>
          </>
        }
      />

      {error && (
        <ErrorState
          title="Dashboard Connection Alert"
          message={error}
          onRetry={fetchDashboard}
        />
      )}

      {/* SECTION 1: 7 KPI Cards Grid */}
      <KpiGrid metrics={data.kpis} />

      {/* SECTION 2: Recharts Visualizations Grid 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DepartmentAttendanceChart data={data.attendanceComparison} />
        <MonthlyTrendChart data={data.monthlyTrend} />
      </div>

      {/* SECTION 3: Recharts Visualizations Grid 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CertificationTrainingChart data={data.trainingCertData} />
        <FacultyWorkloadChart data={data.workloadData} />
      </div>

      {/* SECTION 4: Critical Operational Alerts */}
      <AlertCenter alerts={data.alerts} />

      {/* SECTION 5: Centers of Excellence Summary */}
      <CoeSummary coeSummaries={data.coeSummaries} />
    </div>
  );
}
