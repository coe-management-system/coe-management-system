# COE Management System
## Member 4 — Frontend, Dashboards & Decision Visualization
### Day 1 Progress Documentation

**Date:** 12 August 2026  
**Branch:** `feature/member4-day1-frontend`  
**Status:** Day 1 implementation completed and pushed to GitHub  

---

### 1. Objective

The objective of Member 4's Day 1 scope was to establish the initial Next.js frontend foundation, management user interface, and decision support analytics shell for the Center of Excellence (COE) Management System.

The frontend serves as the primary operational workspace for academic leaders, department heads, faculty mentors, and students. Today's target was to deliver a production-oriented Next.js application foundation structured around a clean architecture (`Next.js App Router -> Centralized API Layer -> FastAPI -> PostgreSQL`), establishing core management interfaces (`/dashboard`, `/students`, `/students/[id]`, `/departments`, `/batches`, `/groups`) alongside standardized placeholder routes for future operational modules. The implementation is intentionally focused on solidifying the Day 1 frontend architectural foundation rather than completing end-to-end backend data pipelines.

---

### 2. Completed Scope

* **Next.js Frontend Foundation**: Preserved and enhanced Next.js 14 App Router project setup with React, TypeScript, and Tailwind CSS.
* **Application Layout**: Built unified layout architecture consisting of a persistent fixed `Sidebar`, global top `Header`, and responsive main content viewport (`AppShell.tsx`).
* **Operational Dashboard**: Implemented interactive operational dashboard (`/dashboard`) featuring 7 KPI cards, 4 Recharts data visualizations, a critical alert center, and a Center of Excellence partner summary grid.
* **Searchable/Filterable Student Directory**: Developed comprehensive student inventory view (`/students`) supporting real-time text search and multi-criteria filtering (Department, Batch, Group).
* **Student 360 Profile View**: Built detailed student operational profile page (`/students/[id]`) displaying academic performance, 360 Industry Readiness index, subject-level attendance, enrolled CoE tracks, verified industry credentials, and skill matrix.
* **Academic Departments Management**: Created Department directory page (`/departments`) displaying Department Name, Code, Description, Head of Department, Student Count, and Faculty Count.
* **Academic Batches Management**: Created Batches directory page (`/batches`) displaying Batch Name, Academic Year, Department, and Enrolled Students.
* **Section Groups Management**: Created Section Groups directory page (`/groups`) displaying Group Name, Batch, Department, and Group Size.
* **Centralized API Abstraction Layer**: Built `src/lib/api.ts` supporting backend REST endpoint contracts (`GET /api/v1/students`, `GET /api/v1/departments`, `GET /api/v1/batches`, `GET /api/v1/groups`, `GET /api/v1/faculty`) with environment variable configuration (`NEXT_PUBLIC_API_URL`) and automatic mock fallback when backend services are offline.
* **TypeScript Type System**: Standardized backend-compatible data models (`src/types/student.ts`, `src/types/index.ts`) matching FastAPI response schemas (`id`, `roll_no`, `name`, `email`, `department_id`, `batch_id`, `group_id`).
* **UI Operational States**: Implemented explicit Loading (`"Loading students..."`), Error (`"Unable to load students. Try again."`), and Empty (`"No students found."`) states on the Students management interface.
* **Future Module Shell Placeholders**: Created 12 standardized shell placeholder routes (`/attendance`, `/training`, `/certification`, `/timetable`, `/workload`, `/scheduling`, `/imports`, `/what-if`, `/ai-assistant`, `/coe`, `/reports`, `/settings`).
* **Frontend Build & Verification**: Achieved 0 TypeScript compilation errors and 0 build errors across 23 static App Router pages.

---

### 3. Application Layout

The frontend application uses a structured, persistent layout architecture wrapped by `src/components/layout/AppShell.tsx`:

* **Sidebar Navigation (`src/components/layout/Sidebar.tsx`)**: Fixed left navigation panel containing institutional branding ("Center of Excellence Ops"), mobile backdrop drawer controls, active route highlighting, category badges, and navigation links for all 17 system modules.
* **Top Header (`src/components/layout/Header.tsx`)**: Global top utility bar featuring global search input, quick action shortcuts, notification center dropdown with badge counters, user profile dropdown (Dr. Rajesh Sharma, System Administrator), and mobile navigation hamburger toggle.
* **Main Content Area**: Responsive container (`flex-1 overflow-y-auto`) wrapping page views with consistent padding and smooth transitions.
* **Page Header Utility (`src/components/ui/PageHeader.tsx`)**: Reusable header component across all pages providing page title, descriptive subtitle, dynamic breadcrumbs, and contextual action buttons.

---

### 4. Dashboard

The Operational Dashboard (`/dashboard`) provides a centralized operational cockpit for academic leadership and CoE program directors.

#### KPI Metric Cards Grid (`src/components/dashboard/KpiGrid.tsx`)
* **Students**: `1,250` (*+8.4% YoY, Across 6 departments*)
* **Faculty**: `85` (*84% Capacity Utilized, Optimal teaching load*)
* **Departments**: `6` (*Active Academic Units: CSE, ECE, IT, ME, CE, EE*)
* **Training Programs**: `12` (*+4 Upcoming CoE Partner Tracks*)
* **Certifications**: `8` (*89% Pass Rate, Palo Alto & Red Hat Tracks*)
* **Average Attendance**: `91.4%` (*+2.1% this month, Target threshold: 85%*)
* **Critical Alerts**: `3 High` (*Requires Attention, Operational & compliance*)

#### Interactive Recharts Visualizations
1. **Department Attendance Comparison (`src/components/charts/DepartmentAttendanceChart.tsx`)**: Bar chart comparing department average attendance rates against institutional targets (Computer Science: 94.2%, IT: 92.5%, Electronics: 89.8%, Mechanical: 87.1%, Civil: 86.4%).
2. **Monthly Attendance & Training Trend (`src/components/charts/MonthlyTrendChart.tsx`)**: Area/Line dual chart tracking attendance rates (88.5% to 91.4%) and training completion rates (68% to 89%) across Feb–Jul.
3. **CoE Certification & Training Progress (`src/components/charts/CertificationTrainingChart.tsx`)**: Horizontal bar chart comparing enrolled vs certified counts across tracks (Cybersecurity, Cloud & Linux, Full Stack, Data Science & AI, IoT).
4. **Faculty Workload Allocation (`src/components/charts/FacultyWorkloadChart.tsx`)**: Bar chart illustrating allocated vs capacity teaching hours by department.

#### Operational Alert Center & CoE Summary
* **Alert Center (`src/components/dashboard/AlertCenter.tsx`)**: High-priority notifications highlighting attendance drops, lab capacity bottlenecks, and pending certification verifications.
* **CoE Partner Summaries (`src/components/dashboard/CoeSummary.tsx`)**: Status overview for Palo Alto Networks CoE (Premier Academy Partner, 380 enrolled) and Red Hat Academy CoE (Gold Regional Hub, 310 enrolled).

---

### 5. Students Management

The Students Management page (`/students`) serves as the primary directory and operational registry for all enrolled students.

* **Route**: `/students`
* **Table View (`src/components/students/StudentTable.tsx`)**: Displays Roll Number (`roll_no`), Student Name, Email, Department, Batch, Group, Overall Attendance Percentage, CoE Credentials Count, and Profile View Actions.
* **Search & Multi-Filtering (`src/components/students/StudentFilters.tsx`)**: Real-time search by name, roll number, or email combined with instant multi-dropdown filtering by Department (All, Computer Science, Information Tech, Electronics, Mechanical, Civil), Batch (All, 2026, 2025, 2024-2028, 2023-2027, 2022-2026), and Section Group (All, A1, A2, B1, B2, CSE-4A, CSE-4B).
* **API Integration**: Fetches student records dynamically via `api.getStudents(params)` from `src/lib/api.ts`.
* **Explicit UI Operational States**:
  * **Loading State**: Displays spinner with message `"Loading students..."`
  * **Error State**: Displays alert container with message `"Unable to load students. Try again."` and a `"Try again"` retry button.
  * **Empty State**: Displays alert container with message `"No students found."` when search or filter criteria return zero records.
* **Offline Mock Fallback**: When the backend server is unreachable, `api.getStudents()` gracefully serves normalized student records from `src/lib/mock-data/students.ts`.

---

### 6. Student Profile / Student 360

The Student Profile view (`/students/[id]`) provides a comprehensive 360-degree operational breakdown for an individual student.

* **Route**: `/students/[id]`
* **Header 360 Card**: Student avatar, full name, status badge (Active), readiness grade (Grade A+), Roll Number, System ID, email, phone, department badge, batch, group, and report audit status (Verified).
* **Industry Readiness Index**: Overall Employability & Skill Index score (e.g., 92/100), breakdown of Technical Proficiency (94%), Aptitude & Problem Solving (90%), Soft Skills & Communication (92%), and qualitative placement recommendation.
* **Academic Attendance Breakdown**: Subject-level attendance breakdown displaying attended vs total classes, percentage progress bar, and color-coded status indicators.
* **Enrolled CoE Training Tracks**: Enrolled track cards detailing track name, provider (e.g., Palo Alto Networks CoE), completion progress percentage, status (Completed / In Progress), and enrollment date.
* **Verified Industry Credentials**: Verified certification badges displaying credential title, issuing body (e.g., Palo Alto Networks, Red Hat), issue date, credential ID, and active status.
* **Skills Matrix**: Tag cloud displaying verified student competencies (Cybersecurity, Python, React, Data Structures, PostgreSQL, Network Defense).
* **Not-Found Handling**: Displays a user-friendly "Student Profile Not Found" state if an invalid student ID is passed in the URL.

---

### 7. Departments

The Departments page (`/departments`) manages institutional academic department records.

* **Route**: `/departments`
* **Data Table View**: Displays Department Code (`code`), Department Name (`name`), Description (`description`), Head of Department (`head`), Total Enrolled Students (`studentCount`), and Total Faculty Count (`facultyCount`).
* **Data Source**: Fetches department list via `api.getDepartments()` from `src/lib/api.ts` with mock fallback (`MOCK_DEPARTMENTS`).
* **Files Used**: `src/app/departments/page.tsx`, `src/lib/api.ts`.

---

### 8. Batches

The Batches page (`/batches`) manages academic student cohorts.

* **Route**: `/batches`
* **Data Table View**: Displays Batch Name (`name`), Academic Year (`year`), Department (`department`), and Total Enrolled Students (`studentCount`).
* **Data Source**: Fetches batch list via `api.getBatches()` from `src/lib/api.ts` with mock fallback (`MOCK_BATCHES`).
* **Files Used**: `src/app/batches/page.tsx`, `src/lib/api.ts`.

---

### 9. Groups

The Groups page (`/groups`) manages student section groupings.

* **Route**: `/groups`
* **Data Table View**: Displays Group Name (`name`), Associated Batch (`batch`), Department (`department`), and Group Size (`studentCount`).
* **Data Source**: Fetches section group list via `api.getGroups()` from `src/lib/api.ts` with mock fallback (`MOCK_GROUPS`).
* **Files Used**: `src/app/groups/page.tsx`, `src/lib/api.ts`.

---

### 10. API Layer

The frontend implements a centralized API abstraction layer located at `src/lib/api.ts`. API calls are strictly routed through this service abstraction rather than being embedded directly inside UI pages or components.

#### Target System Architecture
```
Next.js Page / Component
        ↓
src/lib/api.ts
        ↓
FastAPI (http://127.0.0.1:8000)
        ↓
SQLAlchemy ORM
        ↓
PostgreSQL Database
```

#### Implemented REST API Functions
* `api.getStudents(params)`: Calls `GET ${API_BASE_URL}/api/v1/students`
* `api.getStudentById(id)`: Calls `GET ${API_BASE_URL}/api/v1/students/:id`
* `api.getDepartments()`: Calls `GET ${API_BASE_URL}/api/v1/departments`
* `api.getBatches()`: Calls `GET ${API_BASE_URL}/api/v1/batches`
* `api.getGroups()`: Calls `GET ${API_BASE_URL}/api/v1/groups`
* `api.getFaculty()`: Calls `GET ${API_BASE_URL}/api/v1/faculty`
* `api.getDashboardData()`: Returns operational KPIs, charts, alerts, and CoE summaries.

#### Environment Configuration
The backend base URL is dynamically resolved using an environment variable with a default local fallback:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
```
When the FastAPI backend server is offline or unreachable during development, all API functions catch the network exception and gracefully fall back to structured local mock datasets, ensuring zero UI crashes.

---

### 11. TypeScript Types

All frontend data structures are strictly typed using TypeScript interfaces matching FastAPI Pydantic backend schemas.

#### Primary Type Definitions (`src/types/student.ts` & `src/types/index.ts`)
* **`Student` Interface**:
  * `id`: `number | string`
  * `roll_no`: `string` *(Backend standard)*
  * `rollNumber`: `string` *(Compatibility alias)*
  * `name`: `string`
  * `email`: `string`
  * `department_id`: `number | string`
  * `batch_id`: `number | string`
  * `group_id`: `number | string`
  * `department`: `string`
  * `batch`: `string`
  * `group`: `string`
  * `phone`: `string`
  * `status`: `'Active' | 'On Leave' | 'Graduated'`
  * `attendancePercentage`: `number`
  * `subjectAttendance`: `Array<{ subjectCode, subjectName, attended, total, percentage }>`
  * `trainingTracks`: `Array<{ id, name, provider, progress, status, enrolledDate }>`
  * `certifications`: `Array<{ id, name, issuingBody, issueDate, credentialId, status }>`
  * `readiness`: `{ overallScore, grade, technicalRating, aptitudeRating, softSkillsRating, recommendation }`
  * `skills`: `string[]`
  * `reportAuditStatus`: `'Verified' | 'Pending Audit' | 'Requires Review'`
* **`Department` Interface**: `id`, `name`, `code`, `description`, `head`, `studentCount`, `facultyCount`.
* **`Batch` Interface**: `id`, `name`, `year`, `department`, `studentCount`.
* **`Group` Interface**: `id`, `name`, `batch`, `department`, `studentCount`.
* **`Faculty` Interface**: `id`, `name`, `email`, `department`, `role`.

---

### 12. Future Module Routes

To establish a complete institutional system shell, standardized placeholder routes have been created for future development modules using the reusable `PlaceholderModule` component:

* `/attendance`: Attendance Management module placeholder
* `/training`: CoE Training Tracks module placeholder
* `/certification`: Industry Certifications module placeholder
* `/timetable`: Timetable & Scheduling module placeholder
* `/workload`: Faculty Workload Optimization module placeholder
* `/scheduling`: Automated Resource Scheduling module placeholder
* `/imports`: Data Imports & Batch Processing module placeholder
* `/what-if`: What-If Scenario Simulation module placeholder
* `/ai-assistant`: CoE AI Assistant module placeholder
* `/coe`: Center of Excellence Hub placeholder
* `/reports`: Institutional Audit & Reports module placeholder
* `/settings`: System & User Settings module placeholder

Each placeholder page renders a clean institutional card informing users that the module is structured in the system shell architecture and will be connected to backend engines in upcoming sprints.

---

### 13. Testing & Verification

The frontend application underwent strict automated type checks, production build compilation, and HTTP route verification:

* **TypeScript Type Safety Check**: Ran `npx tsc --noEmit` — Result: **0 errors**.
* **Production Static Build**: Ran `npm run build` — Result: **0 build errors** across **23 static App Router pages**.
* **Local Development Server**: Started server via `npm run dev` on `http://localhost:3000` — Result: **Online & Active in 8.2s**.
* **HTTP Route Verification**: Programmatically verified 20 local routes on `http://localhost:3000` (`/`, `/login`, `/dashboard`, `/students`, `/students/STU-2024-001`, `/departments`, `/batches`, `/groups`, `/attendance`, `/training`, `/certification`, `/timetable`, `/workload`, `/scheduling`, `/imports`, `/what-if`, `/ai-assistant`, `/coe`, `/reports`, `/settings`) — Result: **100% returned HTTP 200 OK**.
* **Security Audit**: Verified that NO database drivers (`pg`, `prisma`) or PostgreSQL credentials exist anywhere in the frontend codebase.

---

### 14. Git Status

* **Branch**: `feature/member4-day1-frontend`
* **Commit Hash**: `f0f3af3dc92c8e983b3cbcfe547ea29139100730`
* **Commit Message**: `feat: complete member 4 frontend implementation`
* **Remote Tracking**: Successfully pushed to `https://github.com/coe-management-system/coe-management-system.git` on branch `feature/member4-day1-frontend`.
* **Branch Isolation**: `main` and `develop` branches were **NOT** modified, merged, rebased, or touched.

---

### 15. Files Implemented / Modified

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                     (Root App Router layout)
│   │   ├── page.tsx                       (Root redirect to dashboard)
│   │   ├── globals.css                    (Tailwind & custom design tokens)
│   │   ├── login/page.tsx                 (Login frontend UI with mock auth)
│   │   ├── dashboard/page.tsx             (Operational Analytics Dashboard)
│   │   ├── students/
│   │   │   ├── page.tsx                   (Searchable/Filterable Student Directory)
│   │   │   └── [id]/page.tsx              (Student 360 Profile View)
│   │   ├── departments/page.tsx           (Departments Directory Table)
│   │   ├── batches/page.tsx               (Academic Batches Table) [NEW]
│   │   ├── groups/page.tsx                (Section Groups Table) [NEW]
│   │   ├── imports/page.tsx               (Data Imports Placeholder) [NEW]
│   │   ├── scheduling/page.tsx            (Resource Scheduling Placeholder) [NEW]
│   │   ├── what-if/page.tsx               (What-If Simulation Placeholder) [NEW]
│   │   ├── attendance/page.tsx            (Attendance Placeholder)
│   │   ├── training/page.tsx              (Training Tracks Placeholder)
│   │   ├── certification/page.tsx         (Certifications Placeholder)
│   │   ├── timetable/page.tsx             (Timetable Placeholder)
│   │   ├── workload/page.tsx              (Workload Placeholder)
│   │   ├── ai-assistant/page.tsx          (AI Assistant Placeholder)
│   │   ├── coe/page.tsx                   (Center of Excellence Placeholder)
│   │   ├── reports/page.tsx               (Reports Placeholder)
│   │   └── settings/page.tsx              (Settings Placeholder)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx               (Main container shell)
│   │   │   ├── Sidebar.tsx                (Fixed left navigation)
│   │   │   └── Header.tsx                 (Top bar & search)
│   │   ├── dashboard/
│   │   │   ├── KpiGrid.tsx                (7 KPI cards grid)
│   │   │   ├── AlertCenter.tsx            (Critical operational alerts)
│   │   │   └── CoeSummary.tsx             (CoE partner hubs status)
│   │   ├── charts/
│   │   │   ├── DepartmentAttendanceChart.tsx  (Recharts Bar Chart)
│   │   │   ├── MonthlyTrendChart.tsx          (Recharts Area/Line Chart)
│   │   │   ├── CertificationTrainingChart.tsx (Recharts Horizontal Bar Chart)
│   │   │   └── FacultyWorkloadChart.tsx       (Recharts Bar Chart)
│   │   ├── students/
│   │   │   ├── StudentTable.tsx           (Student inventory table)
│   │   │   ├── StudentFilters.tsx         (Search & dropdown filters)
│   │   │   └── StudentProfileView.tsx     (Student 360 profile layout)
│   │   └── ui/
│   │       ├── PageHeader.tsx             (Header banner & breadcrumbs)
│   │       ├── StatusBadge.tsx            (Status pill indicators)
│   │       └── PlaceholderModule.tsx      (Future module shell container)
│   ├── lib/
│   │   ├── api.ts                         (Unified API abstraction layer) [NEW]
│   │   ├── api/
│   │   │   └── students.ts                (Student API delegate)
│   │   └── mock-data/
│   │       ├── students.ts                (Mock student dataset)
│   │       ├── dashboard.ts               (Mock KPI & chart datasets)
│   │       └── alerts.ts                  (Mock operational alerts)
│   └── types/
│       ├── index.ts                       (Centralized type exports) [NEW]
│       ├── student.ts                     (Backend-compatible schemas)
│       └── dashboard.ts                   (Dashboard metric interfaces)
├── package.json
├── tailwind.config.ts
└── .gitignore
```

---

### 16. Current Limitations

* **Live Backend Service Connection**: While `src/lib/api.ts` is fully wired to call `GET /api/v1/students` at `NEXT_PUBLIC_API_URL` (`http://127.0.0.1:8000`), a live FastAPI backend process was not running locally during Day 1 static compilation; the frontend successfully fell back to normalized mock datasets.
* **Production Authentication**: The `/login` page provides form validation and client-side session state; live OAuth2 / JWT backend token validation is deferred to future sprints.
* **Database Direct Connection**: In strict accordance with system architecture rules, the Next.js frontend contains zero direct PostgreSQL database connections.
* **Future Module Functionality**: Placeholder routes (`/attendance`, `/timetable`, `/workload`, `/scheduling`, `/what-if`, `/ai-assistant`) render shell UI containers pending future backend engine integrations.

---

### 17. Next Development Phase / Work Remaining

#### Immediate Dependencies (Next Sprint)
1. **Live FastAPI Backend Connection**: Connect `src/lib/api.ts` to active FastAPI services running on `http://127.0.0.1:8000`.
2. **PostgreSQL Database Integration**: Verify real student, department, batch, and group records flowing from PostgreSQL through SQLAlchemy into Next.js data tables.
3. **Backend Authentication & JWT Session Store**: Wire `/login` credentials to FastAPI auth endpoints for token storage and role-based route protection.

#### Future Development
1. **Deep Module Implementations**: Expand shell placeholders (`/attendance`, `/training`, `/certification`, `/timetable`, `/workload`, `/scheduling`, `/what-if`, `/ai-assistant`) into full interactive management modules.
2. **End-to-End Integration Testing**: Implement automated Cypress / Playwright E2E tests across frontend and FastAPI backend.

---

### 18. Day 1 Completion Summary

Member 4 has successfully established the complete Next.js frontend foundation, management UI, and operational analytics dashboard for the Center of Excellence Management System during Day 1. By implementing a unified API abstraction layer (`src/lib/api.ts`), backend-compatible TypeScript data models (`roll_no`), robust loading/error/empty UI states, management tables for Students, Departments, Batches, and Groups, interactive Recharts visualizations, and 12 standardized module shell placeholders, the frontend is fully prepared for seamless integration with Member 1's FastAPI backend and Member 2's PostgreSQL database in subsequent development phases.
