# JobHunter AI — Complete Setup Guide

## Step 1: Get Your Groq API Key (Required)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up / Log in
3. Go to API Keys → Create API Key
4. Copy your key

## Step 2: Set Up the Database

### Option A: Local PostgreSQL
```bash
# Install PostgreSQL from https://www.postgresql.org/download/
# Then create the database:
psql -U postgres -c "CREATE DATABASE jobhunter_ai;"
```

### Option B: Supabase (Free cloud PostgreSQL)
1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project
3. Settings → Database → Copy the connection string

## Step 3: Configure Backend

```bash
cd backend
copy .env.example .env
```

Edit `.env` and set at minimum:
```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/jobhunter_ai
JWT_SECRET_KEY=generate-a-random-32-char-string-here
```

## Step 4: Start the Backend

```bash
# Double-click start.bat, OR:
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

The backend creates all database tables automatically on first start.

Verify: http://localhost:8000/health → should return `{"status": "healthy"}`
API Docs: http://localhost:8000/docs

## Step 5: Configure Frontend

```bash
cd frontend
copy .env.example .env.local
```

`.env.local` already defaults to `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Step 6: Start the Frontend

```bash
# Double-click start.bat, OR:
cd frontend
npm run dev
```

App: http://localhost:3000

---

## Step 7: First Use

1. Open http://localhost:3000
2. Click "Create one free" to register
3. Complete the 4-step onboarding wizard
4. Upload your resume in Resume Manager
5. Click "Discover Jobs" to fetch real opportunities
6. Click "Match" on any job for AI compatibility scoring

---

## Adding More Job Sources

### Adzuna (Free tier — 1,000 req/month)
1. Register at [developer.adzuna.com](https://developer.adzuna.com)
2. Get your App ID and App Key
3. Add to `backend/.env`:
   ```
   ADZUNA_APP_ID=your_app_id
   ADZUNA_API_KEY=your_api_key
   ```

### JSearch via RapidAPI (LinkedIn, Indeed, Glassdoor)
1. Subscribe at [rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
2. Get your API key
3. Add to `backend/.env`:
   ```
   JSEARCH_API_KEY=your_rapidapi_key
   ```

### Remotive (Already works — no key needed)
Remote job listings work immediately with no configuration.

---

## Setting Up Gmail Integration

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:8000/api/v1/email/callback`
6. Add to `backend/.env`:
   ```
   GMAIL_CLIENT_ID=your_client_id
   GMAIL_CLIENT_SECRET=your_client_secret
   ```
7. In the app: Settings → Integrations → Connect Gmail

---

## Production Deployment

### Backend → Railway
1. Install Railway CLI: `npm install -g @railway/cli`
2. `railway login`
3. `cd backend && railway init && railway up`
4. Set environment variables in Railway dashboard
5. Add a PostgreSQL plugin in Railway

### Frontend → Vercel
1. Install Vercel CLI: `npm install -g vercel`
2. `cd frontend && vercel --prod`
3. Set `NEXT_PUBLIC_API_URL` to your Railway backend URL

### Database → Supabase
1. Create project at supabase.com
2. Copy connection string to `DATABASE_URL`
3. Run: `alembic upgrade head` from backend directory

---

## Troubleshooting

**"GROQ_API_KEY is not configured"**
→ Add `GROQ_API_KEY=your_key` to `backend/.env`

**"Could not connect to database"**
→ Check `DATABASE_URL` and ensure PostgreSQL is running

**"Resume analysis pending indefinitely"**
→ Check GROQ_API_KEY is set; view logs with `uvicorn --log-level debug`

**Frontend shows "Network Error"**
→ Ensure backend is running on port 8000; check NEXT_PUBLIC_API_URL in `.env.local`
