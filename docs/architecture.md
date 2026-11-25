# JobHunter AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    JobHunter AI Platform                     │
│                                                             │
│  ┌──────────────┐    HTTP/REST    ┌──────────────────────┐  │
│  │   Next.js    │◄───────────────►│      FastAPI         │  │
│  │  Frontend    │                 │      Backend         │  │
│  │  (Port 3000) │                 │    (Port 8000)       │  │
│  └──────────────┘                 └──────────┬───────────┘  │
│                                              │               │
│                              ┌───────────────┼──────────┐   │
│                              │               │          │   │
│                      ┌───────▼─────┐  ┌──────▼───────┐  │   │
│                      │ PostgreSQL  │  │   Groq AI    │  │   │
│                      │  Database  │  │   (Llama 3)  │  │   │
│                      └───────────┘  └─────────────┘  │   │
│                                                        │   │
│                      ┌────────────────────────────┐   │   │
│                      │   Job Sources              │   │   │
│                      │  • Remotive (free)         │   │   │
│                      │  • Adzuna API              │   │   │
│                      │  • JSearch/RapidAPI        │   │   │
│                      └────────────────────────────┘   │   │
└─────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

```
src/
├── app/                     # Next.js App Router
│   ├── (auth)/              # Auth pages (no sidebar)
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── (dashboard)/         # Protected dashboard pages
│   │   ├── overview/        # Main dashboard
│   │   ├── discover-jobs/   # Job search
│   │   ├── recommended-jobs/# AI-ranked jobs
│   │   ├── ai-matching/     # Score breakdown
│   │   ├── applications/    # Table + Kanban tracker
│   │   ├── resume-manager/  # Upload + AI analysis
│   │   ├── ai-assistant/    # Cover letters + app prep
│   │   ├── outreach-studio/ # Email generator (12 types)
│   │   ├── company-intelligence/ # AI company research
│   │   ├── linkedin-outreach/    # LinkedIn messages
│   │   ├── email-campaigns/ # Outreach CRM
│   │   ├── interview-prep/  # AI interview questions
│   │   ├── notifications/   # In-app notifications
│   │   ├── analytics/       # Recharts dashboards
│   │   ├── profile/         # Edit profile
│   │   └── settings/        # Integrations + API keys
│   └── onboarding/          # 4-step setup wizard
├── components/
│   ├── ui/                  # shadcn/ui components
│   └── layout/              # Sidebar, Header, DashboardLayout
├── contexts/AuthContext.tsx  # JWT auth state
├── services/api.ts           # Axios API client (all endpoints)
└── types/index.ts            # 35 TypeScript interfaces
```

## Backend Architecture

```
app/
├── main.py                  # FastAPI app, CORS, lifespan
├── core/
│   ├── config.py            # Pydantic settings from .env
│   ├── database.py          # SQLAlchemy engine + session
│   ├── security.py          # JWT + bcrypt
│   └── deps.py              # FastAPI dependencies
├── api/v1/endpoints/
│   ├── auth.py              # Register, login, JWT
│   ├── profile.py           # Profile CRUD + onboarding
│   ├── resumes.py           # Upload, parse, analyze
│   ├── jobs.py              # List, search, save, match
│   ├── ai.py                # All 9 Groq AI endpoints
│   ├── applications.py      # Application CRUD + status
│   ├── outreach.py          # Outreach CRM + emails
│   ├── analytics.py         # Stats + chart data
│   ├── notifications.py     # In-app notifications
│   └── email_integration.py # Gmail OAuth + send
├── models/                  # 34 SQLAlchemy models
├── services/
│   ├── ai/groq_client.py    # 13 Groq AI functions
│   ├── resumes/             # PDF/DOCX parser + service
│   └── jobs/                # Discovery + dedup + filter
├── integrations/job_sources/
│   ├── base.py              # Abstract connector
│   ├── adzuna.py            # Adzuna API
│   ├── remotive.py          # Remotive (free)
│   └── jsearch.py           # JSearch/RapidAPI
└── tasks/                   # Celery background jobs
```

## Data Flow: Job Discovery → Matching

```
User clicks "Discover Jobs"
        ↓
FastAPI /jobs/discover
        ↓
run_job_discovery() [background]
        ↓
┌──────────────────────────────────────┐
│  For each connector (parallel):      │
│  • AdzunaConnector.search()          │
│  • RemotiveConnector.search()        │
│  • JSearchConnector.search()         │
└────────────────────┬─────────────────┘
                     ↓
     Normalize all listings to JobListing
                     ↓
     Compute MD5 fingerprint (title+company+url)
                     ↓
     Deduplicate against DB
                     ↓
     Save new jobs to PostgreSQL
                     ↓
User clicks "Match" on a job
                     ↓
FastAPI /jobs/{id}/match
                     ↓
     Load user's primary resume + profile
                     ↓
     Groq: analyze_job_description()
                     ↓
     Groq: calculate_job_match()
                     ↓
     Save JobMatch to DB (score 0-100)
                     ↓
     Return full analysis to frontend
```

## Data Flow: AI Email Generation

```
User fills AI Outreach Studio form
        ↓
Frontend POST /ai/generate-email
        ↓
Backend loads candidate profile from DB
(resume + user profile merged)
        ↓
Groq: generate_application_email()
  Input: candidate, company, recipient, job, tone
  Output: 3 subject lines + 3 email lengths + reasoning
        ↓
Return JSON to frontend
        ↓
User selects subject + length + edits
        ↓
"Save to Campaigns" → POST /outreach
        ↓
"Send via Gmail" → POST /email/send
  → Gmail API sends email
  → SentEmail record saved
  → OutreachContact status updated to "sent"
```

## Security Model

- JWT stored in HTTP-only cookies (7-day expiry)
- All AI calls are backend-only — GROQ_API_KEY never reaches browser
- File uploads: type validation + 10MB limit + stored on server filesystem
- All DB queries filter by `user_id` — strict data isolation
- Gmail OAuth: only requested scopes (send, read, compose)
- No automatic email sending — always requires explicit user confirmation
- Passwords: bcrypt with salt (never stored plaintext)
- SQL injection: SQLAlchemy ORM parameterized queries throughout
