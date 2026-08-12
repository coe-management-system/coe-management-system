# AI-Powered Center of Excellence, Academic Operations, Training, Certification & Intelligent Workload Management System

> **Role**: Member 4 — Frontend, Dashboards & Decision Visualization  
> **Phase**: Day 1 Frontend Foundation  
> **Status**: Completed, Built & Verified (0 TypeScript / ESLint / Compilation Errors)

---

## 1. Project Overview

An enterprise-grade academic decision-support platform designed to streamline Center of Excellence tracking, student management, faculty workload distribution, training certifications, and institutional operational analytics.

The system empowers academic leadership and department heads with real-time operational decision support, predictive capacity analytics, and student 360 operational tracking across industry partner tracks (e.g., Palo Alto Networks, Red Hat).

---

## 2. System Architecture

The primary architecture is:

```
Frontend (Next.js)
   ↓
src/lib/api.ts
   ↓
FastAPI (http://127.0.0.1:8000)
   ↓
Application Services
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

Database schema changes are managed using Alembic.

AI functionality follows:

```
User
   ↓
AI Assistant
   ↓
Controlled AI Tools
   ↓
FastAPI
   ↓
Application Services
   ↓
PostgreSQL
```

AI components do not directly access the PostgreSQL database.

---

## 3. Technology Stack

### Frontend
- **Framework**: Next.js 14.2.35 (App Router)
- **Language**: TypeScript 5.x
- **UI Library**: React 19
- **Styling**: Tailwind CSS 3.4.1
- **Icons**: Lucide React (`lucide-react`)
- **Data Visualizations**: Recharts 2.15.1
- **Package Manager**: npm 10.x

### Backend
- **Language**: Python 3.13 / 3.10
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Database**: PostgreSQL
- **Validation**: Pydantic

### Infrastructure & Dev
- **Containers**: Docker / Docker Compose
- **VCS**: Git & GitHub

---

## 4. Repository Structure

```
coe-management-system/
├── README.md
├── .gitignore
├── docker-compose.yml
├── docs/
│   ├── member4-day1-documentation.md
│   └── member4-day1-documentation.docx
├── backend/
│   ├── app/
│   ├── alembic/
│   └── requirements.txt
└── frontend/
    ├── package.json
    ├── next.config.mjs
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
        │   ├── batches/
        │   ├── groups/
        │   ├── imports/
        │   ├── scheduling/
        │   ├── what-if/
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
        │   ├── api.ts
        │   └── mock-data/
        └── types/
            ├── index.ts
            └── student.ts
```

---

## 5. Development Setup & How to Run Locally

### Frontend Setup

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

### Backend Setup

1. **Navigate to backend**:
   ```bash
   cd backend
   python -m venv .venv
   ```

2. **Activate virtual environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start uvicorn server**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 6. Available Frontend Routes

| Route | Purpose | Current Status |
| :--- | :--- | :--- |
| `/login` | Institutional Authentication Portal | **FUNCTIONAL** (Mock Auth) |
| `/dashboard` | Operational Decision Support Dashboard | **FUNCTIONAL** (KPIs & Visualizations) |
| `/students` | Searchable & Filterable Student Directory | **FUNCTIONAL** (API & Mock Fallback) |
| `/students/[id]` | Student 360 Operational Profile | **FUNCTIONAL** (Readiness & Attendance) |
| `/departments` | Department Directory (Code, Name, Description, HOD) | **FUNCTIONAL** |
| `/batches` | Academic Batches (Batch, Year, Department) | **FUNCTIONAL** |
| `/groups` | Student Groups (Group, Batch, Department) | **FUNCTIONAL** |
| `/attendance` | Student & Faculty Attendance | **SHELL PLACEHOLDER** |
| `/training` | CoE Training Programs Catalog | **SHELL PLACEHOLDER** |
| `/certification` | Industry Credential Verification | **SHELL PLACEHOLDER** |
| `/timetable` | Schedule & Timetable Optimization | **SHELL PLACEHOLDER** |
| `/workload` | Faculty Workload & Capacity | **SHELL PLACEHOLDER** |
| `/scheduling` | Automated Resource Scheduling | **SHELL PLACEHOLDER** |
| `/imports` | Data Imports & Processing | **SHELL PLACEHOLDER** |
| `/what-if` | Scenario Simulation Engine | **SHELL PLACEHOLDER** |
| `/coe` | Center of Excellence Hub Management | **SHELL PLACEHOLDER** |
| `/reports` | Institutional Compliance & Exporter | **SHELL PLACEHOLDER** |
| `/ai-assistant` | AI Assistant Query Engine | **SHELL PLACEHOLDER** |
| `/settings` | System Settings & Governance | **SHELL PLACEHOLDER** |

---

## 7. Documentation

Full Member 4 Day 1 Progress Documentation is available in:
- `docs/member4-day1-documentation.md`
- `docs/member4-day1-documentation.docx`
