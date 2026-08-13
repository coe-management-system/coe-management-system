import { api } from '@/lib/api';
import { DashboardData, KpiMetric, OperationalAlert, CoeSummaryData } from '@/types/dashboard';
import {
  MOCK_COE_SUMMARIES,
  MOCK_ATTENDANCE_COMPARISON,
  MOCK_MONTHLY_TREND,
  MOCK_TRAINING_CERT_DATA,
  MOCK_WORKLOAD_DATA,
} from '@/lib/mock-data/dashboard';
import { MOCK_ALERTS } from '@/lib/mock-data/alerts';

export const dashboardApi = {
  async getDashboardData(): Promise<DashboardData> {
    // Concurrently fetch real API data from backend endpoints
    const [students, departments, batches, groups, faculty] = await Promise.all([
      api.getStudents().catch(() => []),
      api.getDepartments().catch(() => []),
      api.getBatches().catch(() => []),
      api.getGroups().catch(() => []),
      api.getFaculty().catch(() => []),
    ]);

    const deptCodes = departments.map((d) => d.code).filter(Boolean).join(', ');
    const batchNames = batches.map((b) => b.name).slice(0, 3).join(', ');
    const groupNames = groups.map((g) => g.name).slice(0, 3).join(', ');

    const kpis: KpiMetric[] = [
      {
        id: 'kpi-students',
        title: 'Students',
        value: students.length.toLocaleString(),
        change: 'Real API Data',
        changeType: 'positive',
        subtitle: `Across ${departments.length} departments`,
        iconName: 'Users',
      },
      {
        id: 'kpi-faculty',
        title: 'Faculty Staff',
        value: faculty.length.toString(),
        change: 'Real API Data',
        changeType: 'positive',
        subtitle: 'Faculty Directory API',
        iconName: 'Briefcase',
      },
      {
        id: 'kpi-departments',
        title: 'Departments',
        value: departments.length.toString(),
        change: 'Active Academic Units',
        changeType: 'positive',
        subtitle: deptCodes || 'Institutional Depts',
        iconName: 'Building2',
      },
      {
        id: 'kpi-batches',
        title: 'Batches / Cohorts',
        value: batches.length.toString(),
        change: 'Active Cohorts',
        changeType: 'positive',
        subtitle: batchNames ? `Cohorts: ${batchNames}` : 'Academic Cohorts',
        iconName: 'Layers',
      },
      {
        id: 'kpi-groups',
        title: 'Section Groups',
        value: groups.length.toString(),
        change: 'Class Sections',
        changeType: 'positive',
        subtitle: groupNames ? `Sections: ${groupNames}` : 'Class Sections',
        iconName: 'FolderTree',
      },
      {
        id: 'kpi-training',
        title: 'Training Programs',
        value: 'Pending API',
        change: 'Backend Pending',
        changeType: 'neutral',
        subtitle: 'Endpoint not available yet',
        iconName: 'BookOpen',
      },
      {
        id: 'kpi-certifications',
        title: 'Certifications',
        value: 'Pending API',
        change: 'Backend Pending',
        changeType: 'neutral',
        subtitle: 'Endpoint not available yet',
        iconName: 'Award',
      },
    ];

    return {
      kpis,
      alerts: MOCK_ALERTS,
      coeSummaries: MOCK_COE_SUMMARIES,
      attendanceComparison: MOCK_ATTENDANCE_COMPARISON,
      monthlyTrend: MOCK_MONTHLY_TREND,
      trainingCertData: MOCK_TRAINING_CERT_DATA,
      workloadData: MOCK_WORKLOAD_DATA,
    };
  },

  async getAlerts(): Promise<OperationalAlert[]> {
    return MOCK_ALERTS;
  },

  async getCoeSummaries(): Promise<CoeSummaryData[]> {
    return MOCK_COE_SUMMARIES;
  },
};