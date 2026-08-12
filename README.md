# AI-Powered Center of Excellence, Academic Operations, Training, Certification & Intelligent Workload Management System

> **Role**: Member 4 — Frontend, Dashboards & Decision Visualization  
> **Phase**: Day 1 Frontend Foundation  
> **Status**: Completed, Built & Verified (0 TypeScript / ESLint / Compilation Errors)

---

## 📌 Official Project Overview

An enterprise-grade academic decision-support platform designed to streamline Center of Excellence tracking, student management, faculty workload distribution, training certifications, and institutional operational analytics.

The system empowers academic leadership and department heads with real-time operational decision support, predictive capacity analytics, and student 360 operational tracking across industry partner tracks (e.g., Palo Alto Networks, Red Hat).

---

## 🎯 Key Objectives

1. **Unified Operational Visibility**: Centralize student throughput, attendance, faculty load, and CoE certification tracking into a single visual dashboard.
2. **Decision Support Analytics**: Provide real-time alerts and Recharts visualizations for proactive capacity planning and resource allocation.
3. **Student 360 Tracking**: Deliver operational profiles detailing attendance metrics, enrolled CoE training tracks, verified credentials, and skill matrices.
4. **Decoupled Architecture**: Abstract all frontend data services via TypeScript interfaces to enable seamless integration with FastAPI backend services.

---

## 🛠️ Technology Stack

- **Framework**: Next.js 14.2.35 (App Router)
- **Language**: TypeScript 5.x
- **UI Library**: React 19
- **Styling**: Tailwind CSS 3.4.1 (Vanilla CSS tokens, zero third-party UI framework dependencies)
- **Icons**: Lucide React (`lucide-react`)
- **Data Visualizations**: Recharts 2.15.1
- **Package Manager**: npm 10.x

---

## 🚀 Current Day 1 Frontend Implementation

- **M4-01 — Next.js Foundation**: Clean Next.js 14 App Router project setup with strict TypeScript configurations and Tailwind CSS.
- **M4-02 — Shared Application Shell**: Enterprise navigation layout featuring responsive sidebar (12 module routes), institutional header, active route tracking, and context isolation for `/login`.
- **M4-03 — Login UI (`/login`)**: Institutional authentication portal with email format and password min-length validation, visibility toggle, error alert state, and mock session redirect.
- **M4-04 — Operational Dashboard (`/dashboard`)**: 7 KPI metric cards, 4 Recharts visual charts (Department Attendance, Monthly Trajectory, Training/Cert Funnel, Faculty Workload), Critical Operational Alerts, and Center of Excellence (Palo Alto & Red Hat) summary blocks.
- **M4-05 — Student Management (`/students` & `/students/[id]`)**: Searchable student directory table with real-time text query search across Name, Roll #, and Email, combined multi-attribute dropdown filters (Department, Batch, Group), data table pagination, and full Student 360 operational profile views.
- **M4-06 — API Service Abstraction**: Strongly-typed TypeScript interfaces (`src/types/`) and decoupled async mock data services (`src/lib/api/`) enabling future backend hookup without UI refactoring.
- **Placeholder Modules**: 10 structural placeholder pages for unbuilt operational modules to prevent 404 navigation errors across all sidebar items.

---

## 📁 Repository Structure

```
coe-management-system/
├── README.md
├── .gitignore
├── docs/
│   ├── DAY_1_DOCUMENTATION.md
│   └── frontend/
│       └── day-1.md
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── postcss.config.mjs
    └── src/
        ├── app/
        │   ├── login/
        │   ├── dashboard/
        │   ├── students/
        │   │   └── [id]/
        │   ├── departments/
        │   ├── attendance/
        │   ├── training/
        │   ├── certification/
        │   ├── timetable/
        │   ├── workload/
        │   ├── coe/
        │   ├── reports/
        │   ├── ai-assistant/
        │   ├── settings/
        │   ├── layout.tsx
        │   ├── page.tsx
        │   └── globals.css
        ├── components/
        │   ├── layout/
        │   ├── ui/
        │   ├── dashboard/
        │   ├── students/
        │   └── charts/
        ├── lib/
        │   ├── api/
        │   └── mock-data/
        └── types/
```

---

## 💻 How to Run Locally

### Prerequisites
- Node.js 18.x or higher
- npm 9.x or higher

### Installation & Running

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

4. **Execute TypeScript typecheck & production build**:
   ```bash
   npx tsc --noEmit
   npm run build
   ```

---

## 🔗 Available Routes

| Route | Purpose | Current Status |
| :--- | :--- | :--- |
| `/login` | Institutional Authentication Portal | **FUNCTIONAL** (Mock Auth) |
| `/dashboard` | Operational Decision Support Dashboard | **FUNCTIONAL** (Mock Data) |
| `/students` | Searchable & Filterable Student Directory | **FUNCTIONAL** (Mock Data) |
| `/students/[id]` | Student 360 Operational Profile | **FUNCTIONAL** (Mock Data) |
| `/departments` | Department Operations | **PLACEHOLDER** |
| `/attendance` | Student & Faculty Attendance | **PLACEHOLDER** |
| `/training` | CoE Training Programs Catalog | **PLACEHOLDER** |
| `/certification` | Industry Credential Verification | **PLACEHOLDER** |
| `/timetable` | Schedule & Timetable Optimization | **PLACEHOLDER** |
| `/workload` | Faculty Workload & Capacity | **PLACEHOLDER** |
| `/coe` | Center of Excellence Hub Management | **PLACEHOLDER** |
| `/reports` | Institutional Compliance & Exporter | **PLACEHOLDER** |
| `/ai-assistant` | AI Assistant Query Engine | **PLACEHOLDER** |
| `/settings` | System Settings & Governance | **PLACEHOLDER** |

---

## ⚠️ Current Limitations

- **Simulated Mock Data Only**: All metrics, student records, attendance figures, and certification counts are simulated in `src/lib/mock-data/`. No live database or backend connection is active in Day 1.
- **Client-Side State**: Authentication state and search filter states exist in client memory and reset upon hard refresh.
- **Placeholder Routes**: 10 remaining modules are structural placeholders displaying "Planned for Future Phase" notices.

---

## 🗺️ Future Development Roadmap

- **Phase 2 — Backend REST API Integration**: Connect `src/lib/api/` services to PostgreSQL databases and FastAPI REST endpoints.
- **Phase 3 — Interactive Module Screens**: Implement full feature UI screens for `/attendance`, `/training`, `/certification`, `/workload`, `/timetable`, and `/coe`.
- **Phase 4 — AI & Optimization Engine**: Implement timetable auto-scheduling algorithms and AI conversational assistant.

---

## 📄 Documentation

For full architectural, component, and API layer documentation, view [docs/DAY_1_DOCUMENTATION.md](file:///C:/Users/Sachin%20Kumar/.gemini/antigravity/scratch/coe-management-system/docs/DAY_1_DOCUMENTATION.md).
