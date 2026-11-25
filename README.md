# JobHunter AI 🚀

> An AI-powered job hunting platform that acts as your personal career agent.
> Powered by **Groq AI**, built with **Next.js + FastAPI + PostgreSQL**.

---

## What It Does

| Module | Capability |
|---|---|
| **Resume Intelligence** | Upload PDF/DOCX → Groq extracts full structured profile |
| **Job Discovery** | Searches Adzuna, Remotive, JSearch for real live jobs |
| **AI Job Matching** | Groq scores every job 0-100 against your resume + profile |
| **AI Application Assistant** | Generates cover letters, customizes resumes, answers form questions |
| **AI Outreach Studio** | Generates 12 email types + LinkedIn messages using Groq |
| **Company Intelligence** | AI researches any company before you reach out |
| **Gmail Integration** | OAuth → create drafts → send approved emails from the app |
| **Application Tracker** | Table + Kanban view of all applications with status updates |
| **Interview Prep** | AI generates technical, behavioral, and company-specific questions |
| **Analytics** | Charts for applications, matches, outreach response rates |

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+ (or Supabase)
- Redis (for background jobs)
- Groq API key → [console.groq.com](https://console.groq.com)

---

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env — set DATABASE_URL, GROQ_API_KEY at minimum

# Create database (PostgreSQL must be running)
# Either: alembic upgrade head
# Or: tables auto-created on first startup

# Start server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
copy .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

App: http://localhost:3000

---

### 3. Docker (Full Stack)

```bash
# From project root
copy backend/.env.example backend/.env
# Edit backend/.env with your keys

docker-compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Required API Keys

| Key | Where to Get | Required |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | **Yes** |
| `DATABASE_URL` | PostgreSQL or Supabase | **Yes** |
| `JWT_SECRET_KEY` | Generate a random string | **Yes** |
| `ADZUNA_APP_ID` + `ADZUNA_API_KEY` | [developer.adzuna.com](https://developer.adzuna.com) | Optional (jobs) |
| `JSEARCH_API_KEY` | [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | Optional (jobs) |
| `GMAIL_CLIENT_ID` + `GMAIL_CLIENT_SECRET` | [Google Cloud Console](https://console.cloud.google.com) | Optional (send emails) |
| `GOOGLE_CLIENT_ID` | [Google Cloud Console](https://console.cloud.google.com) | Optional (OAuth login) |

> **Remotive** (remote jobs) works with no API key.

---

## Project Structure

```
jobhunter-ai/
├── frontend/               # Next.js 14 + TypeScript + Tailwind
│   └── src/
│       ├── app/            # App Router pages
│       │   ├── (auth)/     # Login, Register
│       │   ├── (dashboard)/# All 16 dashboard pages
│       │   └── onboarding/ # 4-step profile setup
│       ├── components/     # UI components (shadcn-based)
│       ├── services/       # API client (axios)
│       ├── contexts/       # Auth context
│       └── types/          # Full TypeScript type definitions
│
├── backend/                # FastAPI + Python 3.12
│   └── app/
│       ├── api/v1/         # 10 REST API routers
│       ├── core/           # Config, DB, Security, Dependencies
│       ├── models/         # 34 SQLAlchemy models
│       ├── services/
│       │   ├── ai/         # Groq AI client (17 functions)
│       │   ├── jobs/       # Job discovery service
│       │   └── resumes/    # Resume parsing service
│       ├── integrations/
│       │   └── job_sources/ # Adzuna, Remotive, JSearch connectors
│       └── main.py
│
├── docs/                   # Architecture + API docs
├── docker-compose.yml
└── README.md
```

---

## AI Functions (Groq)

All powered by `llama-3.1-70b-versatile` (configurable):

- `analyze_resume()` — Extract full profile from resume text
- `extract_candidate_profile()` — Build unified candidate profile
- `analyze_job_description()` — Extract structured job requirements
- `calculate_job_match()` — Score 0-100 with breakdown
- `generate_cover_letter()` — 3 styles, personalized
- `generate_application_email()` — 12 email types, 3 lengths each
- `research_company()` — Company intelligence from web info
- `generate_linkedin_message()` — Connection + follow-up messages
- `generate_interview_questions()` — Full interview prep package
- `generate_resume_customization()` — Keyword-optimize existing resume
- `generate_application_answers()` — Answer application form questions
- `analyze_interview_answer()` — Score + feedback on practice answers

---

## Deployment

### Frontend → Vercel
```bash
cd frontend
vercel --prod
# Set NEXT_PUBLIC_API_URL to your Railway/Render backend URL
```

### Backend → Railway
```bash
# railway.toml already configured
# Set all environment variables in Railway dashboard
railway up
```

### Database → Supabase
1. Create a new Supabase project
2. Copy the connection string to `DATABASE_URL`
3. Run `alembic upgrade head`

---

## Security Notes

- JWT tokens stored in HTTP-only cookies
- GROQ_API_KEY never exposed to frontend
- All file uploads validated (type + size)
- SQL injection protected via SQLAlchemy ORM
- User data isolated — every query filters by `user_id`
- Gmail OAuth — only requested scopes: send, read, compose
- Emails never sent without explicit user confirmation

---

## License

MIT — build your career with it!
