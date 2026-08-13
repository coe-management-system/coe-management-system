import { DashboardData, OperationalAlert, CoeSummaryData } from '@/types/dashboard';
import {
  MOCK_KPIS,
  MOCK_COE_SUMMARIES,
  MOCK_ATTENDANCE_COMPARISON,
  MOCK_MONTHLY_TREND,
  MOCK_TRAINING_CERT_DATA,
  MOCK_WORKLOAD_DATA,
} from '@/lib/mock-data/dashboard';
import { MOCK_ALERTS } from '@/lib/mock-data/alerts';
import { mockApiCall } from './client';

export const dashboardApi = {
  async getDashboardData(): Promise<DashboardData> {
    return mockApiCall<DashboardData>({
      kpis: MOCK_KPIS,
      alerts: MOCK_ALERTS,
      coeSummaries: MOCK_COE_SUMMARIES,
      attendanceComparison: MOCK_ATTENDANCE_COMPARISON,
      monthlyTrend: MOCK_MONTHLY_TREND,
      trainingCertData: MOCK_TRAINING_CERT_DATA,
      workloadData: MOCK_WORKLOAD_DATA,
    });
  },

  async getAlerts(): Promise<OperationalAlert[]> {
    return mockApiCall<OperationalAlert[]>(MOCK_ALERTS);
  },

  async getCoeSummaries(): Promise<CoeSummaryData[]> {
    return mockApiCall<CoeSummaryData[]>(MOCK_COE_SUMMARIES);
  },
};
