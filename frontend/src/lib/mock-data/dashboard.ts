import {
  KpiMetric,
  CoeSummaryData,
  AttendanceComparisonData,
  MonthlyTrendData,
  TrainingCertData,
  WorkloadData,
} from '@/types/dashboard';

export const MOCK_KPIS: KpiMetric[] = [
  {
    id: 'kpi-1',
    title: 'Students',
    value: '1,250',
    change: '+8.4% YoY',
    changeType: 'positive',
    subtitle: 'Across 6 departments',
    iconName: 'Users',
  },
  {
    id: 'kpi-2',
    title: 'Faculty',
    value: '85',
    change: '84% Capacity Utilized',
    changeType: 'neutral',
    subtitle: 'Optimal teaching load',
    iconName: 'Briefcase',
  },
  {
    id: 'kpi-3',
    title: 'Departments',
    value: '6',
    change: 'Active Academic Units',
    changeType: 'positive',
    subtitle: 'CSE, ECE, IT, ME, CE, EE',
    iconName: 'Building2',
  },
  {
    id: 'kpi-4',
    title: 'Training Programs',
    value: '12',
    change: '+4 Upcoming',
    changeType: 'positive',
    subtitle: 'CoE Partner Tracks',
    iconName: 'BookOpen',
  },
  {
    id: 'kpi-5',
    title: 'Certifications',
    value: '8',
    change: '89% Pass Rate',
    changeType: 'positive',
    subtitle: 'Palo Alto & Red Hat Tracks',
    iconName: 'Award',
  },
  {
    id: 'kpi-6',
    title: 'Average Attendance',
    value: '91.4%',
    change: '+2.1% this month',
    changeType: 'positive',
    subtitle: 'Target threshold: 85%',
    iconName: 'CalendarCheck',
  },
  {
    id: 'kpi-7',
    title: 'Critical Alerts',
    value: '3 High',
    change: 'Requires Attention',
    changeType: 'negative',
    subtitle: 'Operational & compliance',
    iconName: 'AlertTriangle',
  },
];

export const MOCK_COE_SUMMARIES: CoeSummaryData[] = [
  {
    id: 'coe-palo-alto',
    name: 'Palo Alto Networks CoE',
    vendor: 'Palo Alto Networks',
    partnerLevel: 'Premier Academy Partner',
    activeTracks: 6,
    enrolledStudents: 380,
    certificationsCompleted: 184,
    labUtilizationRate: 92,
    leadFaculty: 'Prof. Robert Vance',
    status: 'active',
  },
  {
    id: 'coe-red-hat',
    name: 'Red Hat Academy CoE',
    vendor: 'Red Hat Enterprise',
    partnerLevel: 'Gold Regional Hub',
    activeTracks: 5,
    enrolledStudents: 310,
    certificationsCompleted: 158,
    labUtilizationRate: 88,
    leadFaculty: 'Dr. Anita Sharma',
    status: 'expanding',
  },
];

export const MOCK_ATTENDANCE_COMPARISON: AttendanceComparisonData[] = [
  { department: 'Computer Science', averageAttendance: 94.2, targetAttendance: 88.0 },
  { department: 'Information Tech', averageAttendance: 92.5, targetAttendance: 88.0 },
  { department: 'Electronics', averageAttendance: 89.8, targetAttendance: 85.0 },
  { department: 'Mechanical', averageAttendance: 87.1, targetAttendance: 85.0 },
  { department: 'Civil', averageAttendance: 86.4, targetAttendance: 85.0 },
];

export const MOCK_MONTHLY_TREND: MonthlyTrendData[] = [
  { month: 'Feb', overallAttendance: 88.5, trainingCompletion: 68 },
  { month: 'Mar', overallAttendance: 89.2, trainingCompletion: 74 },
  { month: 'Apr', overallAttendance: 90.1, trainingCompletion: 79 },
  { month: 'May', overallAttendance: 91.0, trainingCompletion: 83 },
  { month: 'Jun', overallAttendance: 90.8, trainingCompletion: 86 },
  { month: 'Jul', overallAttendance: 91.4, trainingCompletion: 89 },
];

export const MOCK_TRAINING_CERT_DATA: TrainingCertData[] = [
  { category: 'Cybersecurity (Palo Alto)', enrolled: 220, certified: 140 },
  { category: 'Cloud & Linux (Red Hat)', enrolled: 190, certified: 115 },
  { category: 'Full Stack Web Dev', enrolled: 280, certified: 185 },
  { category: 'Data Science & AI', enrolled: 160, certified: 95 },
  { category: 'IoT & Embedded Hardware', enrolled: 130, certified: 70 },
];

export const MOCK_WORKLOAD_DATA: WorkloadData[] = [
  { department: 'Computer Science', allocatedHours: 420, capacityHours: 480, facultyCount: 24 },
  { department: 'Information Tech', allocatedHours: 350, capacityHours: 400, facultyCount: 20 },
  { department: 'Electronics', allocatedHours: 310, capacityHours: 360, facultyCount: 18 },
  { department: 'Mechanical', allocatedHours: 280, capacityHours: 340, facultyCount: 17 },
  { department: 'Civil', allocatedHours: 240, capacityHours: 300, facultyCount: 15 },
];
