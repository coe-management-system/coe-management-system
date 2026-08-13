export interface Student {
  id: number | string;
  roll_no?: string;
  rollNumber?: string; // Compatibility alias
  name: string;
  email: string;
  department_id?: number | string;
  batch_id?: number | string;
  group_id?: number | string;
  department: string;
  batch: string;
  group: string;
  phone?: string;
  status?: 'Active' | 'On Leave' | 'Graduated';
  attendancePercentage?: number;
  subjectAttendance?: Array<{
    subjectCode: string;
    subjectName: string;
    attended: number;
    total: number;
    percentage: number;
  }>;
  trainingTracks?: Array<{
    id: string;
    name: string;
    provider: string;
    progress: number;
    status: 'In Progress' | 'Completed' | 'Upcoming';
    enrolledDate: string;
  }>;
  certifications?: Array<{
    id: string;
    name: string;
    issuingBody: string;
    issueDate: string;
    expiryDate?: string;
    badgeUrl?: string;
    credentialId: string;
    status: 'Active' | 'Pending Verification' | 'Expired';
  }>;
  readiness?: {
    overallScore: number;
    grade: 'A+' | 'A' | 'B+' | 'B' | 'C';
    technicalRating: number;
    aptitudeRating: number;
    softSkillsRating: number;
    recommendation: string;
  };
  skills?: string[];
  reportAuditStatus?: 'Verified' | 'Pending Audit' | 'Requires Review';
  lastActive?: string;
}

export interface Department {
  id: number | string;
  name: string;
  code: string;
  description: string;
  head?: string;
  studentCount?: number;
  facultyCount?: number;
}

export interface Batch {
  id: number | string;
  name: string;
  year: number | string;
  department_id?: number | string;
  department: string;
  studentCount?: number;
}

export interface Group {
  id: number | string;
  name: string;
  batch_id?: number | string;
  batch: string;
  department: string;
  studentCount?: number;
}

export interface Faculty {
  id: number | string;
  employee_code?: string;
  name: string;
  email: string;
  department_id?: number | string;
  department: string;
  role?: string;
}

export type DepartmentType =
  | 'Computer Science'
  | 'Electronics'
  | 'Information Tech'
  | 'Mechanical'
  | 'Civil'
  | 'CSE'
  | 'ECE'
  | 'IT'
  | 'ME'
  | 'CE';

export type BatchType = '2023-2027' | '2024-2028' | '2022-2026' | '2026' | '2025';
export type GroupType = 'A1' | 'A2' | 'B1' | 'B2' | 'CSE-4A' | 'CSE-4B' | '4A' | '4B';

export interface StudentFilterParams {
  searchQuery?: string;
  department?: string;
  batch?: string;
  group?: string;
}