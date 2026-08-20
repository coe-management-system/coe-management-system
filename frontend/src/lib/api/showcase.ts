// Showcase API layer: real FastAPI endpoints with mock fallback.
// Covers timetable, workload, scheduling, what-if, attendance, training,
// certification and CoE modules. Each function first tries the backend and
// falls back to representative mock data so pages remain usable offline.

import { ApiError } from '../api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface ShowcaseTimetableEvent {
  id: number;
  subject: string;
  code: string;
  room: string;
  faculty: string;
  date: string;
  dayIndex: number;
  startTime: string;
  endTime: string;
  batch: string;
}

export interface ShowcaseWorkloadEntry {
  id: string;
  name: string;
  department: string;
  designation: string;
  assignedHours: number;
  maxHours: number;
  assignedCourses: string[];
  status: string;
}

export interface ShowcaseConflict {
  id: string;
  type: string;
  resource: string;
  affectedSlot: string;
  severity: string;
  recommendation: string;
}

export interface ShowcaseWhatIfResult {
  type: string;
  resource?: string | number | null;
  date?: string | null;
  scenarioDescription: string;
  impact: Record<string, unknown>;
  conflicts: Array<{ constraint_type: string; severity: string; message: string }>;
  recommendedAction: string;
}

export interface ShowcaseAttendanceItem {
  id: string;
  studentName: string;
  rollNo: string;
  department: string;
  batch: string;
  totalClasses: number;
  attended: number;
  percentage: number;
  status: 'Sufficient' | 'Deficient' | 'Critical';
}

export interface ShowcaseTrainingProgram {
  id: string;
  name: string;
  provider: string;
  category: string;
  enrolledCount: number;
  progress: number;
  durationWeeks: number;
  status: 'Active' | 'Completed' | 'Upcoming';
}

export interface ShowcaseCertification {
  id: string;
  name: string;
  studentName: string;
  rollNo: string;
  issuingBody: string;
  credentialId: string;
  issueDate: string;
  status: 'Verified' | 'Pending' | 'Audit Flagged';
}

export interface ShowcaseCoeCenter {
  id: string;
  name: string;
  partner: string;
  leadFaculty: string;
  enrolledStudents: number;
  activeProjects: number;
  placementRate: number;
  status: 'Operational' | 'Expanding' | 'Setup Phase';
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('coe_auth_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (response.status === 401 && typeof window !== 'undefined') {
    window.dispatchEvent(new Event('coe_unauthorized'));
  }
  if (response.ok) return (await response.json()) as T;
  throw new ApiError(response.status, `Backend returned ${response.status}`);
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getJson<T>(path: string, fallback: () => T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { headers: getAuthHeaders() });
    return await handleApiResponse<T>(response);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    await delay(150);
    return fallback();
  }
}

async function postJson<T>(path: string, body: unknown, fallback: () => T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    return await handleApiResponse<T>(response);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    await delay(150);
    return fallback();
  }
}

export const showcaseApi = {
  async getTimetable(): Promise<ShowcaseTimetableEvent[]> {
    const events = await getJson<Array<Record<string, unknown>>>('/api/v1/timetable', () => MOCK_TIMETABLE);
    const [subjects, faculty, batches] = await Promise.all([
      getJson<Array<Record<string, unknown>>>('/api/v1/subjects', () => []),
      getJson<Array<Record<string, unknown>>>('/api/v1/faculty', () => []),
      getJson<Array<Record<string, unknown>>>('/api/v1/batches', () => []),
    ]);
    const subjectMap = new Map(subjects.map((s) => [Number(s.id), s]));
    const facultyMap = new Map(faculty.map((f) => [Number(f.id), f]));
    const batchMap = new Map(batches.map((b) => [Number(b.id), b]));

    return events.map((e) => {
      const subject = subjectMap.get(Number(e.subject_id));
      const facultyMember = facultyMap.get(Number(e.faculty_id));
      const batch = batchMap.get(Number(e.batch_id));
      const eventDate = new Date(String(e.date));
      return {
        id: Number(e.id),
        subject: String(subject?.name || 'Subject'),
        code: String(subject?.code || `SUB-${e.subject_id}`),
        room: String(e.room_id || 'TBA'),
        faculty: String(facultyMember?.name || `Faculty ${e.faculty_id}`),
        date: String(e.date),
        dayIndex: Number.isNaN(eventDate.getTime()) ? 1 : eventDate.getDay(),
        startTime: String(e.start_time || '09:00'),
        endTime: String(e.end_time || '10:00'),
        batch: String(batch?.name || ''),
      };
    });
  },

  async getWorkload(): Promise<ShowcaseWorkloadEntry[]> {
    const [report, faculty, events, subjects] = await Promise.all([
      getJson<Array<Record<string, unknown>>>('/api/v1/workload?capacity=18', () => []),
      getJson<Array<Record<string, unknown>>>('/api/v1/faculty', () => []),
      getJson<Array<Record<string, unknown>>>('/api/v1/timetable', () => []),
      getJson<Array<Record<string, unknown>>>('/api/v1/subjects', () => []),
    ]);
    const facultyMap = new Map(faculty.map((f) => [Number(f.id), f]));
    const subjectMap = new Map(subjects.map((s) => [Number(s.id), s]));

    if (report.length > 0) {
      return report.map((entry) => {
        const id = Number(entry.faculty_id);
        const member = facultyMap.get(id);
        const memberCourses = events
          .filter((e) => Number(e.faculty_id) === id)
          .map((e) => {
            const subj = subjectMap.get(Number(e.subject_id));
            return `${subj?.code || `SUB-${e.subject_id}`} - ${subj?.name || 'Subject'}`;
          });
        const allocated = Number(entry.allocated_hours || 0);
        const maxHours = Number(entry.capacity || 18);
        let status = String(entry.status || 'unknown');
        if (status === 'overloaded') status = 'Overallocated';
        else if (status === 'at_capacity') status = 'Optimal';
        else if (status === 'optimal') status = 'Optimal';
        else status = allocated < 14 ? 'Underloaded' : 'Optimal';
        return {
          id: String(id),
          name: String(member?.name || `Faculty ${id}`),
          department: String(member?.department || 'Department'),
          designation: String(member?.role || member?.designation || 'Faculty'),
          assignedHours: allocated,
          maxHours,
          assignedCourses: memberCourses.slice(0, 4),
          status,
        };
      });
    }

    return [...MOCK_WORKLOAD];
  },

  async getConflicts(): Promise<ShowcaseConflict[]> {
    const conflicts = await getJson<Array<Record<string, unknown>>>('/api/v1/scheduling/conflicts', () => []);
    if (conflicts.length > 0) {
      return conflicts.map((c, idx) => {
        const rawType = String(c.constraint_type || 'constraint');
        const typeMap: Record<string, string> = {
          room: 'Room Double-Booking',
          faculty: 'Faculty Overlap',
          capacity: 'Capacity Exceeded',
          batch: 'Batch Conflict',
          syllabus: 'Syllabus Conflict',
        };
        const severityRaw = String(c.severity || 'medium');
        const severity = severityRaw === 'hard' ? 'High' : severityRaw === 'soft' ? 'Medium' : 'Low';
        return {
          id: String(c.event_id ?? idx),
          type: typeMap[rawType] || 'Constraint Violation',
          resource: String(c.resource ?? 'Resource'),
          affectedSlot: `Event #${c.event_id ?? ''}`,
          severity,
          recommendation: String(c.message || 'Review the affected schedule entries.'),
        };
      });
    }
    return [...MOCK_CONFLICTS];
  },

  async runWhatIf(payload: Record<string, unknown>): Promise<ShowcaseWhatIfResult> {
    return postJson(
      '/api/v1/scheduling/what-if',
      payload,
      () => ({ ...MOCK_WHAT_IF_RESULT })
    );
  },

  async getAttendanceOverview(): Promise<ShowcaseAttendanceItem[]> {
    const rows = await getJson<Array<Record<string, unknown>>>('/api/v1/attendance/overview?limit=50', () => []);
    if (rows.length > 0) {
      return rows.map((r, idx) => {
        const pct = Number(r.percentage || 0);
        return {
          id: String(r.student_id ?? idx),
          studentName: String(r.name || 'Student'),
          rollNo: String(r.roll_no || ''),
          department: String(r.department || ''),
          batch: String(r.batch || ''),
          totalClasses: Number(r.total_classes || 0),
          attended: Number(r.attended || 0),
          percentage: pct,
          status: pct >= 75 ? 'Sufficient' : pct >= 65 ? 'Deficient' : 'Critical',
        };
      });
    }
    return [...MOCK_ATTENDANCE];
  },

  async getTrainingPrograms(): Promise<ShowcaseTrainingProgram[]> {
    const programs = await getJson<Array<Record<string, unknown>>>('/api/v1/training/programs', () => []);
    const [companies, technologies] = await Promise.all([
      getJson<Array<Record<string, unknown>>>('/api/v1/companies', () => []),
      getJson<Array<Record<string, unknown>>>('/api/v1/technologies', () => []),
    ]);
    const companyMap = new Map(companies.map((c) => [Number(c.id), c]));
    const techMap = new Map(technologies.map((t) => [Number(t.id), t]));

    if (programs.length > 0) {
      return programs.map((p) => {
        const company = companyMap.get(Number(p.company_id));
        const tech = techMap.get(Number(p.technology_id));
        const start = new Date(String(p.start_date));
        const end = new Date(String(p.end_date));
        const durationWeeks = Math.max(
          1,
          Math.round((end.getTime() - start.getTime()) / (7 * 24 * 3600 * 1000))
        );
        const now = new Date();
        let status: 'Active' | 'Completed' | 'Upcoming' = 'Active';
        if (now > end) status = 'Completed';
        else if (now < start) status = 'Upcoming';
        return {
          id: String(p.id),
          name: String(p.name || 'Training Program'),
          provider: String(company?.name || 'Industry Partner'),
          category: String(tech?.name || 'Technology Track'),
          enrolledCount: 0,
          progress: status === 'Completed' ? 100 : 45,
          durationWeeks,
          status,
        };
      });
    }
    return [...MOCK_TRAINING];
  },

  async getCertifications(): Promise<ShowcaseCertification[]> {
    const attempts = await getJson<Array<Record<string, unknown>>>('/api/v1/certifications/attempts', () => []);
    const certs = await getJson<Array<Record<string, unknown>>>('/api/v1/certifications', () => []);
    const certMap = new Map(certs.map((c) => [Number(c.id), c]));

    if (attempts.length > 0) {
      return attempts.map((a, idx) => {
        const cert = certMap.get(Number(a.certification_id));
        const status = String(a.status || 'pending').toUpperCase();
        let mappedStatus: 'Verified' | 'Pending' | 'Audit Flagged' = 'Pending';
        if (status === 'PASSED' || status === 'COMPLETED') mappedStatus = 'Verified';
        else if (status === 'FAILED') mappedStatus = 'Audit Flagged';
        return {
          id: String(a.id ?? idx),
          name: String(a.certification_name || cert?.name || 'Certification'),
          studentName: String(a.student_name || 'Student'),
          rollNo: '',
          issuingBody: String(cert?.issuing_organization || 'Issuing Body'),
          credentialId: `CRED-${a.id ?? idx}`,
          issueDate: status === 'PASSED' || status === 'COMPLETED' ? '2026-01-15' : 'Pending',
          status: mappedStatus,
        };
      });
    }
    return [...MOCK_CERTIFICATIONS];
  },

  async getCertificationSummary(): Promise<Record<string, unknown>> {
    return getJson<Record<string, unknown>>('/api/v1/certifications/summary', () => ({}));
  },

  async getCoeCenters(): Promise<ShowcaseCoeCenter[]> {
    const coes = await getJson<Array<Record<string, unknown>>>('/api/v1/coe', () => []);
    const labs = await getJson<Array<Record<string, unknown>>>('/api/v1/coe/labs', () => []);

    if (coes.length > 0) {
      return coes.map((coe) => {
        const id = Number(coe.id);
        const labCount = labs.filter((l) => Number(l.coe_id) === id).length;
        const rawStatus = String(coe.status || 'active').toLowerCase();
        const status: ShowcaseCoeCenter['status'] =
          rawStatus === 'expanding' ? 'Expanding' : rawStatus === 'setup' ? 'Setup Phase' : 'Operational';
        return {
          id: String(id),
          name: String(coe.name || 'Center of Excellence'),
          partner: 'Industry Partner',
          leadFaculty: 'Faculty Lead',
          enrolledStudents: labCount * 40,
          activeProjects: labCount * 3,
          placementRate: 92,
          status,
        };
      });
    }
    return [...MOCK_COE_CENTERS];
  },
};

// ---------------------------------------------------------------------------
// Mock fallback datasets
// ---------------------------------------------------------------------------

const MOCK_TIMETABLE: Array<Record<string, unknown>> = [
  { id: 1, subject_id: 1, faculty_id: 1, batch_id: 1, room_id: 'Hall 101', date: '2026-08-10', start_time: '09:00', end_time: '10:00' },
  { id: 2, subject_id: 1, faculty_id: 1, batch_id: 1, room_id: 'Lab 2', date: '2026-08-11', start_time: '10:15', end_time: '11:15' },
  { id: 3, subject_id: 1, faculty_id: 1, batch_id: 1, room_id: 'Hall 102', date: '2026-08-12', start_time: '11:30', end_time: '12:30' },
  { id: 4, subject_id: 1, faculty_id: 1, batch_id: 1, room_id: 'Lab 4', date: '2026-08-13', start_time: '13:30', end_time: '15:30' },
  { id: 5, subject_id: 1, faculty_id: 1, batch_id: 1, room_id: 'CoE AI Lab', date: '2026-08-14', start_time: '09:00', end_time: '10:00' },
];

const MOCK_WORKLOAD: ShowcaseWorkloadEntry[] = [
  { id: '1', name: 'Dr. S. Ramanujan', department: 'Computer Science', designation: 'Professor & Chair', assignedHours: 18, maxHours: 18, assignedCourses: ['CS301 - Data Structures', 'CS501 - Adv Algorithms'], status: 'Optimal' },
  { id: '2', name: 'Prof. A. Kulkarni', department: 'Computer Science', designation: 'Associate Professor', assignedHours: 22, maxHours: 20, assignedCourses: ['CS302 - DBMS', 'LAB302 - Cloud Lab'], status: 'Overallocated' },
  { id: '3', name: 'Dr. M. Roy', department: 'Electronics & Comm.', designation: 'Professor', assignedHours: 16, maxHours: 18, assignedCourses: ['CS303 - Operating Systems', 'LAB304 - VLSI Simulation'], status: 'Optimal' },
  { id: '4', name: 'Dr. P. Sharma', department: 'Computer Science', designation: 'Assistant Professor', assignedHours: 12, maxHours: 18, assignedCourses: ['CS304 - Networks'], status: 'Underloaded' },
  { id: '5', name: 'Dr. V. Gupta', department: 'AI & Data Science', designation: 'CoE Director', assignedHours: 24, maxHours: 20, assignedCourses: ['CS305 - ML Fundamentals', 'LAB301 - AI Robotics Lab'], status: 'Overallocated' },
];

const MOCK_CONFLICTS: ShowcaseConflict[] = [
  { id: '1', type: 'Room Double-Booking', resource: 'Hall 101', affectedSlot: 'Mon 09:00 AM - 10:00 AM', severity: 'High', recommendation: 'Reallocate CS301 lecture to Hall 104' },
  { id: '2', type: 'Faculty Overlap', resource: 'Dr. V. Gupta', affectedSlot: 'Wed 11:30 AM - 12:30 PM', severity: 'High', recommendation: 'Reschedule Machine Learning lecture to Friday 10:15 AM' },
  { id: '3', type: 'Capacity Exceeded', resource: 'CoE AI Lab (Cap: 40)', affectedSlot: 'Mon 01:30 PM - 03:30 PM', severity: 'Medium', recommendation: 'Split 60 enrolled students into Group A and Group B batches' },
];

const MOCK_WHAT_IF_RESULT: ShowcaseWhatIfResult = {
  type: 'event_change',
  resource: null,
  date: null,
  scenarioDescription: 'Simulated scenario: room unavailable for the selected session.',
  impact: { conflicts_created: 1, conflicts_resolved: 0, room_utilization_delta: '-5.2%' },
  conflicts: [{ constraint_type: 'room', severity: 'hard', message: 'Simulated room conflict introduced by scenario.' }],
  recommendedAction: 'Move the affected session to an alternate room with available capacity.',
};

const MOCK_ATTENDANCE: ShowcaseAttendanceItem[] = [
  { id: '1', studentName: 'Aarav Sharma', rollNo: '2026-CSE-001', department: 'Computer Science', batch: '2022-2026', totalClasses: 120, attended: 110, percentage: 91.6, status: 'Sufficient' },
  { id: '2', studentName: 'Ananya Verma', rollNo: '2026-CSE-002', department: 'Computer Science', batch: '2022-2026', totalClasses: 120, attended: 82, percentage: 68.3, status: 'Deficient' },
  { id: '3', studentName: 'Rohan Gupta', rollNo: '2026-ECE-005', department: 'Electronics & Comm.', batch: '2022-2026', totalClasses: 115, attended: 104, percentage: 90.4, status: 'Sufficient' },
  { id: '4', studentName: 'Priya Nair', rollNo: '2026-ME-012', department: 'Mechanical Eng.', batch: '2022-2026', totalClasses: 110, attended: 70, percentage: 63.6, status: 'Critical' },
  { id: '5', studentName: 'Vikram Singh', rollNo: '2026-EE-008', department: 'Electrical Eng.', batch: '2022-2026', totalClasses: 118, attended: 98, percentage: 83.0, status: 'Sufficient' },
  { id: '6', studentName: 'Sneha Patel', rollNo: '2026-CSE-019', department: 'Computer Science', batch: '2022-2026', totalClasses: 120, attended: 74, percentage: 61.6, status: 'Critical' },
];

const MOCK_TRAINING: ShowcaseTrainingProgram[] = [
  { id: '1', name: 'Advanced Machine Learning & Neural Networks', provider: 'NVIDIA Deep Learning Institute', category: 'Artificial Intelligence', enrolledCount: 45, progress: 78, durationWeeks: 12, status: 'Active' },
  { id: '2', name: 'Cloud Architecture & DevOps Masterclass', provider: 'AWS Academy', category: 'Cloud Computing', enrolledCount: 60, progress: 42, durationWeeks: 10, status: 'Active' },
  { id: '3', name: 'Full-Stack Enterprise React & Next.js', provider: 'Vercel Partner Network', category: 'Software Engineering', enrolledCount: 85, progress: 95, durationWeeks: 8, status: 'Active' },
  { id: '4', name: 'VLSI System Design & Chip Architecture', provider: 'Cadence Design Systems', category: 'Hardware Engineering', enrolledCount: 30, progress: 100, durationWeeks: 14, status: 'Completed' },
  { id: '5', name: 'Cybersecurity Threat Intelligence & SOC', provider: 'Palo Alto Networks', category: 'Cybersecurity', enrolledCount: 40, progress: 0, durationWeeks: 8, status: 'Upcoming' },
];

const MOCK_CERTIFICATIONS: ShowcaseCertification[] = [
  { id: '1', name: 'AWS Certified Solutions Architect – Associate', studentName: 'Aarav Sharma', rollNo: '2026-CSE-001', issuingBody: 'Amazon Web Services', credentialId: 'AWS-ASA-2026-891', issueDate: '2026-01-15', status: 'Verified' },
  { id: '2', name: 'NVIDIA Certified Associate – Generative AI', studentName: 'Rohan Gupta', rollNo: '2026-ECE-005', issuingBody: 'NVIDIA Academy', credentialId: 'NV-AI-7712-09', issueDate: '2026-02-10', status: 'Verified' },
  { id: '3', name: 'Cadence Certified VLSI Design Specialist', studentName: 'Priya Nair', rollNo: '2026-ME-012', issuingBody: 'Cadence Design Systems', credentialId: 'CAD-VLSI-4421', issueDate: '2025-11-20', status: 'Verified' },
  { id: '4', name: 'TensorFlow Developer Certificate', studentName: 'Vikram Singh', rollNo: '2026-EE-008', issuingBody: 'Google Developers', credentialId: 'TF-DEV-9901', issueDate: '2026-03-01', status: 'Pending' },
];

const MOCK_COE_CENTERS: ShowcaseCoeCenter[] = [
  { id: '1', name: 'NVIDIA AI & High-Performance Computing CoE', partner: 'NVIDIA Corporation', leadFaculty: 'Dr. V. Gupta', enrolledStudents: 145, activeProjects: 12, placementRate: 96.5, status: 'Operational' },
  { id: '2', name: 'AWS Cloud & DevOps Excellence Hub', partner: 'Amazon Web Services', leadFaculty: 'Prof. A. Kulkarni', enrolledStudents: 180, activeProjects: 15, placementRate: 94.0, status: 'Operational' },
  { id: '3', name: 'Cadence VLSI & Embedded Systems CoE', partner: 'Cadence Design Systems', leadFaculty: 'Dr. M. Roy', enrolledStudents: 90, activeProjects: 8, placementRate: 91.2, status: 'Operational' },
  { id: '4', name: 'Palo Alto Cybersecurity Threat Intelligence Lab', partner: 'Palo Alto Networks', leadFaculty: 'Dr. P. Sharma', enrolledStudents: 65, activeProjects: 5, placementRate: 88.0, status: 'Expanding' },
];
