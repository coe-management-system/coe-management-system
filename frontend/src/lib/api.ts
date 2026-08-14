// Unified API Layer for Center of Excellence Management System
// Architected for FastAPI backend REST integration, Auth JWT Token Propagation, & Centralized Error Handling
// Standardized endpoints: GET/POST /api/v1/auth/*, GET/POST /api/v1/students, GET /api/v1/departments, GET /api/v1/batches, GET /api/v1/groups, GET /api/v1/faculty, POST /api/v1/imports/excel

import { Student, Department, Batch, Group, Faculty, StudentFilterParams } from '@/types';
import { MOCK_STUDENTS } from './mock-data/students';
import { MOCK_KPIS, MOCK_COE_SUMMARIES, MOCK_ATTENDANCE_COMPARISON, MOCK_MONTHLY_TREND, MOCK_TRAINING_CERT_DATA, MOCK_WORKLOAD_DATA } from './mock-data/dashboard';
import { MOCK_ALERTS } from './mock-data/alerts';
import { DashboardData } from '@/types/dashboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Centralized Frontend API Error Representation
export class ApiError extends Error {
  statusCode: number;

  constructor(statusCode: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

// Centralized HTTP Status Error Mapping
export function getErrorMessageForStatus(status: number): string {
  switch (status) {
    case 401:
      return 'Authentication required. Please log in with valid credentials.';
    case 403:
      return 'Access denied. You do not have permission to view or modify this resource.';
    case 404:
      return 'The requested resource was not found on the institutional server.';
    case 409:
      return 'Roll number already exists.';
    case 422:
      return 'Invalid request payload or data validation error.';
    case 500:
      return 'Internal server error occurred on the institutional backend.';
    default:
      return `Institutional server returned error status (${status}). Please try again.`;
  }
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('coe_auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

// Centralized Response Validator & Parser
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('coe_unauthorized'));
    }
  }

  if (response.ok) {
    return (await response.json()) as T;
  }

  const message = getErrorMessageForStatus(response.status);
  throw new ApiError(response.status, message);
}

// Default mock datasets for backend fallback
export const MOCK_DEPARTMENTS: Department[] = [
  { id: 1, name: 'Computer Science & Engineering', code: 'CSE', description: 'Computer Science and Engineering Department', head: 'Dr. Ramesh Kumar', studentCount: 450, facultyCount: 28 },
  { id: 2, name: 'Electronics & Communication', code: 'ECE', description: 'Electronics and Communication Engineering Department', head: 'Dr. Sunita Sharma', studentCount: 320, facultyCount: 22 },
  { id: 3, name: 'Information Technology', code: 'IT', description: 'Information Technology & Software Systems', head: 'Dr. Amit Patel', studentCount: 280, facultyCount: 18 },
  { id: 4, name: 'Mechanical Engineering', code: 'ME', description: 'Mechanical & Automation Engineering Department', head: 'Dr. Rajesh Verma', studentCount: 220, facultyCount: 15 },
  { id: 5, name: 'Civil Engineering', code: 'CE', description: 'Civil Infrastructure & Structural Engineering', head: 'Dr. Priya Kulkarni', studentCount: 150, facultyCount: 12 },
];

export const MOCK_BATCHES: Batch[] = [
  { id: 1, name: '2026', year: 2026, department: 'CSE', studentCount: 120 },
  { id: 2, name: '2025', year: 2025, department: 'CSE', studentCount: 110 },
  { id: 3, name: '2024-2028', year: '2024-2028', department: 'CSE', studentCount: 115 },
  { id: 4, name: '2023-2027', year: '2023-2027', department: 'ECE', studentCount: 95 },
  { id: 5, name: '2022-2026', year: '2022-2026', department: 'IT', studentCount: 88 },
];

export const MOCK_GROUPS: Group[] = [
  { id: 1, name: 'CSE-4A', batch: '2026', department: 'CSE', studentCount: 60 },
  { id: 2, name: 'CSE-4B', batch: '2026', department: 'CSE', studentCount: 60 },
  { id: 3, name: 'ECE-3A', batch: '2025', department: 'ECE', studentCount: 50 },
  { id: 4, name: 'IT-2B', batch: '2024-2028', department: 'IT', studentCount: 45 },
];

export const MOCK_FACULTY: Faculty[] = [
  { id: 1, name: 'Dr. Ramesh Kumar', email: 'ramesh.kumar@institution.edu', department: 'CSE', role: 'Professor & HOD' },
  { id: 2, name: 'Dr. Sunita Sharma', email: 'sunita.sharma@institution.edu', department: 'ECE', role: 'Associate Professor' },
  { id: 3, name: 'Prof. Alok Gupta', email: 'alok.gupta@institution.edu', department: 'IT', role: 'Assistant Professor' },
];

const DEPT_MAP: Record<number, string> = {
  1: 'CSE',
  2: 'ECE',
  3: 'IT',
  4: 'ME',
  5: 'CE',
};

const BATCH_MAP: Record<number, string> = {
  1: '2026',
  2: '2025',
  3: '2024-2028',
  4: '2023-2027',
  5: '2022-2026',
};

const GROUP_MAP: Record<number, string> = {
  1: 'CSE-4A',
  2: 'CSE-4B',
  3: 'ECE-3A',
  4: 'IT-2B',
};

// Helper to ensure backend-compatible fields exist on student objects
function normalizeStudent(s: Record<string, unknown>): Student {
  const roll = String(s.roll_no || s.rollNumber || s.rollNo || '');
  const name = String(s.name || '');
  const email = String(s.email || '');
  const deptId = Number(s.department_id);
  const batchId = Number(s.batch_id);
  const groupId = Number(s.group_id);

  const department = String(
    s.department || s.department_name || DEPT_MAP[deptId] || (deptId ? `Dept #${deptId}` : 'CSE')
  );
  const batch = String(
    s.batch || s.batch_name || BATCH_MAP[batchId] || (batchId ? `Batch #${batchId}` : '2026')
  );
  const group = String(
    s.group || s.group_name || GROUP_MAP[groupId] || (groupId ? `Group #${groupId}` : 'CSE-4A')
  );
  const id = (s.id as string | number) || roll || 'STU-0';

  return {
    ...(s as unknown as Student),
    id,
    name,
    email,
    roll_no: roll,
    rollNumber: roll,
    department_id: s.department_id as number | undefined,
    batch_id: s.batch_id as number | undefined,
    group_id: s.group_id as number | undefined,
    department,
    batch,
    group,
  };
}

function normalizeDepartment(item: Record<string, unknown>): Department {
  const id = (item.id as number | string) || 1;
  const name = String(item.name || 'Department');
  const code = String(item.code || name.substring(0, 3).toUpperCase());
  const description = String(item.description || `${name} Department`);
  const head = String(item.head || 'To be appointed');
  const studentCount = Number(item.studentCount || item.student_count || 120);
  const facultyCount = Number(item.facultyCount || item.faculty_count || 15);

  return { id, name, code, description, head, studentCount, facultyCount };
}

function normalizeBatch(item: Record<string, unknown>): Batch {
  const id = (item.id as number | string) || 1;
  const name = String(item.name || '2026');
  const year = (item.year as number | string) || '2026';
  const deptId = Number(item.department_id);
  const department = String(
    item.department || item.department_name || DEPT_MAP[deptId] || (deptId ? `Dept #${deptId}` : 'CSE')
  );
  const studentCount = Number(item.studentCount || item.student_count || 100);

  return { id, name, year, department_id: item.department_id as number | undefined, department, studentCount };
}

function normalizeGroup(item: Record<string, unknown>): Group {
  const id = (item.id as number | string) || 1;
  const name = String(item.name || 'CSE-4A');
  const batchId = Number(item.batch_id);
  const batch = String(
    item.batch || item.batch_name || BATCH_MAP[batchId] || (batchId ? `Batch #${batchId}` : '2026')
  );
  const department = String(item.department || DEPT_MAP[batchId] || 'CSE');
  const studentCount = Number(item.studentCount || item.student_count || 50);

  return { id, name, batch_id: item.batch_id as number | undefined, batch, department, studentCount };
}

function normalizeFaculty(item: Record<string, unknown>): Faculty {
  const id = (item.id as number | string) || 1;
  const employeeCode = String(item.employee_code || item.employeeCode || `FAC-${id}`);
  const name = String(item.name || 'Faculty Member');
  const email = String(item.email || '');
  const deptId = Number(item.department_id);
  const department = String(
    item.department || item.department_name || DEPT_MAP[deptId] || (deptId ? `Dept #${deptId}` : 'CSE')
  );
  const role = String(item.role || item.designation || 'Faculty');

  return { id, employee_code: employeeCode, name, email, department_id: item.department_id as number | undefined, department, role };
}

export interface StudentCreatePayload {
  roll_no: string;
  name: string;
  email: string;
  department_id: number;
  batch_id: number;
  group_id: number;
}

export interface ImportResultSummary {
  filename: string;
  import_id: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  imported_students: number;
  skipped_students: number;
  validation_errors: Array<{ row?: number; message?: string; field?: string; [key: string]: unknown }>;
  reference_errors: Array<{ row?: number; message?: string; field?: string; [key: string]: unknown }>;
}

export const api = {
  // AUTH: POST /api/v1/auth/login
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return handleApiResponse<{ access_token: string; token_type: string }>(response);
  },

  // AUTH: GET /api/v1/auth/me
  async getMe(token?: string): Promise<{ id: number; username: string; email: string; role_id: number }> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const authToken = token || (typeof window !== 'undefined' ? localStorage.getItem('coe_auth_token') : null);
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers,
    });
    return handleApiResponse<{ id: number; username: string; email: string; role_id: number }>(response);
  },

  // GET /api/v1/students
  async getStudents(params?: StudentFilterParams): Promise<Student[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/students`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      const data = await handleApiResponse<Record<string, unknown>[]>(response);
      const normalized = Array.isArray(data) ? data.map(normalizeStudent) : [];
      return filterStudents(normalized, params);
    } catch (err) {
      if (err instanceof ApiError) {
        throw err;
      }
      await new Promise((resolve) => setTimeout(resolve, 150));
      const normalizedMock = MOCK_STUDENTS.map((item) => normalizeStudent(item as unknown as Record<string, unknown>));
      return filterStudents(normalizedMock, params);
    }
  },

  // GET /api/v1/students/:id
  async getStudentById(id: string): Promise<Student | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/students/${id}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      const data = await handleApiResponse<Record<string, unknown>>(response);
      return normalizeStudent(data);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.statusCode === 404) return null;
        throw err;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 100));
    const found = MOCK_STUDENTS.find(
      (s) => s.id === id || s.rollNumber === id || s.roll_no === id
    );
    return found ? normalizeStudent(found as unknown as Record<string, unknown>) : null;
  },

  // POST /api/v1/students
  async createStudent(payload: StudentCreatePayload): Promise<Student> {
    const response = await fetch(`${API_BASE_URL}/api/v1/students`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await handleApiResponse<Record<string, unknown>>(response);
    return normalizeStudent(data);
  },

  // POST /api/v1/imports/excel
  async importExcel(file: File): Promise<ImportResultSummary> {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('coe_auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/imports/excel`, {
      method: 'POST',
      headers,
      body: formData,
    });

    return handleApiResponse<ImportResultSummary>(response);
  },

  // GET /api/v1/departments
  async getDepartments(): Promise<Department[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/departments`, { headers: getAuthHeaders() });
      const data = await handleApiResponse<Record<string, unknown>[]>(response);
      return Array.isArray(data) ? data.map(normalizeDepartment) : [];
    } catch (err) {
      if (err instanceof ApiError) throw err;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
    return MOCK_DEPARTMENTS;
  },

  // GET /api/v1/batches
  async getBatches(): Promise<Batch[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/batches`, { headers: getAuthHeaders() });
      const data = await handleApiResponse<Record<string, unknown>[]>(response);
      return Array.isArray(data) ? data.map(normalizeBatch) : [];
    } catch (err) {
      if (err instanceof ApiError) throw err;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
    return MOCK_BATCHES;
  },

  // GET /api/v1/groups
  async getGroups(): Promise<Group[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/groups`, { headers: getAuthHeaders() });
      const data = await handleApiResponse<Record<string, unknown>[]>(response);
      return Array.isArray(data) ? data.map(normalizeGroup) : [];
    } catch (err) {
      if (err instanceof ApiError) throw err;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
    return MOCK_GROUPS;
  },

  // GET /api/v1/faculty
  async getFaculty(): Promise<Faculty[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/faculty`, { headers: getAuthHeaders() });
      const data = await handleApiResponse<Record<string, unknown>[]>(response);
      return Array.isArray(data) ? data.map(normalizeFaculty) : [];
    } catch (err) {
      if (err instanceof ApiError) throw err;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
    return MOCK_FACULTY.map((item) => normalizeFaculty(item as unknown as Record<string, unknown>));
  },

  // GET Dashboard Data
  async getDashboardData(): Promise<DashboardData> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      kpis: MOCK_KPIS,
      alerts: MOCK_ALERTS,
      coeSummaries: MOCK_COE_SUMMARIES,
      attendanceComparison: MOCK_ATTENDANCE_COMPARISON,
      monthlyTrend: MOCK_MONTHLY_TREND,
      trainingCertData: MOCK_TRAINING_CERT_DATA,
      workloadData: MOCK_WORKLOAD_DATA,
    };
  },
};

function filterStudents(list: Student[], params?: StudentFilterParams): Student[] {
  if (!params) return list;
  return list.filter((student) => {
    if (params.searchQuery) {
      const q = params.searchQuery.toLowerCase();
      const nameMatch = student.name.toLowerCase().includes(q);
      const rollMatch = (student.roll_no || student.rollNumber || '').toLowerCase().includes(q);
      const emailMatch = student.email.toLowerCase().includes(q);
      if (!nameMatch && !rollMatch && !emailMatch) return false;
    }
    if (params.department && params.department !== 'All') {
      if (!student.department.toLowerCase().includes(params.department.toLowerCase())) return false;
    }
    if (params.batch && params.batch !== 'All') {
      if (!student.batch.toString().includes(params.batch.toString())) return false;
    }
    if (params.group && params.group !== 'All') {
      if (!student.group.toString().toLowerCase().includes(params.group.toString().toLowerCase())) return false;
    }
    return true;
  });
}
