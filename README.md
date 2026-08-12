# COE Management System

A centralized management system for managing academic, student, faculty, attendance, training, certification, timetable, workload, data import, analytics, scheduling, and AI-assisted operations.

## 1. Project Overview

The COE Management System is designed to provide a centralized platform for managing academic and administrative data that is currently distributed across spreadsheets, manual processes, and separate systems.

The system provides:

- Student management
- Department, batch, and group management
- Faculty management
- Subject management
- Attendance management
- Training management
- Certification tracking
- Timetable management
- Faculty workload management
- Excel data import and normalization
- Analytics
- Scheduling and conflict detection
- What-if scheduling simulation
- AI-assisted queries and recommendations
- Reporting
- Controlled communication workflows

## 2. System Architecture

The primary architecture is:

```
Frontend
   ↓
FastAPI
   ↓
Application Services
   ↓
SQLAlchemy
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

## 3. Technology Stack

### Backend
- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic

### Frontend
- Next.js
- TypeScript

### Infrastructure
- Docker
- Docker Compose

### Development
- Git
- GitHub
- Pytest

## 4. Repository Structure

```
coe-management-system/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── docs/
├── backend/
├── frontend/
├── data/
├── database/
├── algorithms/
├── tests/
└── infrastructure/
```

Detailed architecture is documented in `docs/`.

## 5. Backend Structure

The backend follows a layered architecture:

```
API Routes
   ↓
Schemas
   ↓
Services
   ↓
SQLAlchemy Models
   ↓
PostgreSQL
```

Major backend modules include:

- Authentication
- Students
- Organization
- Attendance
- Training
- Certification
- Timetable
- Workload
- Excel integration
- Analytics
- Scheduling
- AI
- Communications

## 6. Development Setup

### Clone the repository

```bash
git clone <repository-url>
cd coe-management-system
```

### Backend setup

```bash
cd backend
python -m venv .venv
```

**Windows:**

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment configuration

Create a `.env` file using `.env.example` as a reference.

Example:

```
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/coe_management
SECRET_KEY=development-secret
```

Never commit `.env`.

### Database migration

From the backend directory:

```bash
alembic upgrade head
```

### Start the backend

```bash
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000`

Swagger documentation: `http://127.0.0.1:8000/docs`

## 7. Database Migration Workflow

Database changes must follow:

```
SQLAlchemy Model
      ↓
Alembic Revision
      ↓
Review Migration
      ↓
Alembic Upgrade
      ↓
PostgreSQL
```

Example:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Migration files must be reviewed before being applied.

## 8. Git Workflow

The main branches are:

- `main`
- `develop`

Feature development uses:

- `feature/member1-backend`
- `feature/member2-excel`
- `feature/member3-scheduling`
- `feature/member4-frontend`
- `feature/member5-ai`

Feature branches are merged into `develop`.

Production-ready changes are merged from `develop` into `main`.

## 9. Documentation

Project documentation is organized into:

```
docs/
├── requirements/
├── architecture/
└── research/
```

## 10. Project Status

The project is under active development.

Current initial development focus:

- Backend foundation
- Database schema
- API contracts
- Excel integration
- Scheduling prototype
- Frontend prototype
- AI tool prototype

## 11. Security Principles

- Secrets must not be committed to Git.
- Database credentials must be stored in environment variables.
- AI components must not directly access the database.
- Database access must go through application-controlled services.
- Authentication and authorization will be enforced at the API layer.
- Sensitive operations should require appropriate permissions.
- Production credentials must never be stored in source code.

## 12. License

See [LICENSE](./LICENSE).

## 13. Project Scope

### 13.1 Purpose

The purpose of the COE Management System is to provide a centralized platform for managing academic and administrative operations.

The system will replace or reduce dependency on manually maintained spreadsheets and disconnected processes.

### 13.2 Primary Objectives

The system aims to:

1. Centralize institutional data.
2. Provide controlled access to academic and administrative information.
3. Standardize Excel-based data imports.
4. Provide student and faculty management.
5. Track attendance, training, and certifications.
6. Manage timetables and faculty workload.
7. Detect scheduling conflicts.
8. Provide analytics for decision-making.
9. Support what-if scheduling scenarios.
10. Provide controlled AI-assisted access to institutional information.

### 13.3 Core Domains

The system consists of the following domains:

**Organization**
- Users
- Roles
- Departments
- Batches
- Groups
- Faculty

**Academic**
- Students
- Subjects
- Attendance

**Training**
- Training programs
- Training sessions

**Certification**
- Certifications
- Certification attempts

**Scheduling**
- Timetable events
- Faculty workload
- Scheduling constraints
- Conflict detection
- Rescheduling
- What-if simulation

**Data Integration**
- Excel reading
- Column detection
- Column mapping
- Normalization
- Validation
- Duplicate detection
- Import processing

**Analytics**
- Attendance analytics
- Syllabus analytics
- Training analytics
- Certification analytics
- Workload analytics
- Student performance

**AI**
- AI assistant
- Query engine
- Recommendations
- Controlled tools

**Communication**
- Email drafting
- Recipient resolution
- Approval workflows

### 13.4 Initial Prototype Scope

The initial prototype will prioritize:

- PostgreSQL database
- SQLAlchemy models
- Alembic migrations
- FastAPI backend
- Student APIs
- Organization APIs
- Excel prototype
- Scheduling prototype
- Frontend dashboard prototype
- AI tool prototype

### 13.5 Out of Scope for Initial Prototype

The following features are not required for the initial prototype:

- Advanced voice assistant
- Mobile application
- Advanced email automation
- Complex optimization
- Calendar integration
- Production-scale reporting
- Advanced AI agents

These may be implemented in later phases.

### 13.6 Target Users

Potential users include:

- Administrators
- Faculty
- Department coordinators
- Training coordinators
- Academic coordinators
- Students
- Authorized management personnel

### 13.7 Scope Principle

The system should be modular.

New functionality should be added through independent modules without breaking existing functionality.
