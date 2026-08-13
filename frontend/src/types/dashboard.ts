export type AlertSeverity = 'HIGH' | 'MEDIUM' | 'LOW';

export interface KpiMetric {
  id: string;
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  subtitle?: string;
  iconName: string;
}

export interface OperationalAlert {
  id: string;
  title: string;
  description: string;
  severity: AlertSeverity;
  category: string;
  timestamp: string;
  affectedEntity?: string;
  actionRequired?: boolean;
}

export interface CoeSummaryData {
  id: string;
  name: string;
  vendor: string;
  partnerLevel: string;
  activeTracks: number;
  enrolledStudents: number;
  certificationsCompleted: number;
  labUtilizationRate: number;
  leadFaculty: string;
  status: 'active' | 'expanding' | 'maintenance';
}

export interface AttendanceComparisonData {
  department: string;
  averageAttendance: number;
  targetAttendance: number;
}

export interface MonthlyTrendData {
  month: string;
  overallAttendance: number;
  trainingCompletion: number;
}

export interface TrainingCertData {
  category: string;
  enrolled: number;
  certified: number;
}

export interface WorkloadData {
  department: string;
  allocatedHours: number;
  capacityHours: number;
  facultyCount: number;
}

export interface DashboardData {
  kpis: KpiMetric[];
  alerts: OperationalAlert[];
  coeSummaries: CoeSummaryData[];
  attendanceComparison: AttendanceComparisonData[];
  monthlyTrend: MonthlyTrendData[];
  trainingCertData: TrainingCertData[];
  workloadData: WorkloadData[];
}
