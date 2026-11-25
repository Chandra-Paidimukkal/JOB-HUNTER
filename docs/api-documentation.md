# JobHunter AI — API Documentation

Base URL: `http://localhost:8000/api/v1`  
Interactive Docs: `http://localhost:8000/docs`

All endpoints (except `/auth/register` and `/auth/login`) require:
```
Authorization: Bearer <access_token>
```

---

## Authentication

### POST /auth/register
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Smith"
}
```
**Response `201`:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Smith",
    "is_verified": true,
    "onboarding_completed": false
  }
}
```

---

### POST /auth/login
Authenticate and receive a JWT token.

**Request:**
```json
{ "email": "user@example.com", "password": "securepassword123" }
```
**Response `200`:** Same as register.

---

### GET /auth/me
Get current authenticated user.

**Response `200`:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Smith",
  "is_verified": true,
  "onboarding_completed": true
}
```

---

### POST /auth/forgot-password
Trigger password reset email.

**Request:** `{ "email": "user@example.com" }`  
**Response `200`:** `{ "message": "If this email exists, a password reset link has been sent." }`

---

### POST /auth/reset-password
Complete password reset.

**Request:** `{ "token": "reset_token", "password": "newpassword123" }`

---

## Profile

### GET /profile
Get complete user profile including preferences.

**Response `200`:**
```json
{
  "user": { "id": "...", "email": "...", "full_name": "..." },
  "profile": {
    "phone": "+1 555 000 0000",
    "current_location": "New York, USA",
    "current_title": "Senior Software Engineer",
    "current_company": "Acme Corp",
    "total_experience_years": 5.0,
    "technical_skills": ["Python", "React", "PostgreSQL"],
    "soft_skills": ["Leadership", "Communication"],
    "linkedin_url": "https://linkedin.com/in/...",
    "willing_to_relocate": true
  },
  "preferences": {
    "preferred_titles": ["Software Engineer", "Tech Lead"],
    "preferred_countries": ["USA", "UK"],
    "remote_ok": true,
    "expected_salary": 150000,
    "currency": "USD"
  }
}
```

---

### PUT /profile
Update user profile fields.

**Request:** Any subset of profile fields.

---

### PUT /profile/preferences
Update job search preferences.

---

### POST /profile/onboarding
Complete the onboarding wizard (4 steps combined).

**Request:**
```json
{
  "personal": { "full_name": "...", "phone": "...", "linkedin_url": "..." },
  "professional": { "current_title": "...", "technical_skills": ["..."] },
  "preferences": { "preferred_titles": ["..."], "remote_ok": true },
  "objective": { "career_objective": "...", "short_term_goals": "..." }
}
```

---

## Resumes

### POST /resumes/upload
Upload a PDF or DOCX resume. Triggers AI analysis in background.

**Request:** `multipart/form-data`
- `file`: PDF or DOCX (max 10MB)
- `version_name` (optional): Label for this version

**Response `201`:**
```json
{
  "message": "Resume uploaded. AI analysis running in background.",
  "resume": {
    "id": "uuid",
    "file_name": "resume.pdf",
    "file_type": "pdf",
    "file_size": 142000,
    "is_primary": true,
    "is_analyzed": false,
    "quality_score": null
  }
}
```

---

### GET /resumes
List all user resumes.

---

### GET /resumes/{id}
Get single resume including extracted data.

**Response includes:**
```json
{
  "id": "...",
  "is_analyzed": true,
  "quality_score": 82,
  "extracted_data": {
    "personal_info": { "name": "...", "email": "..." },
    "professional_summary": "...",
    "experience": [{ "company": "...", "title": "...", "achievements": [] }],
    "skills": { "technical": [], "soft": [] },
    "keywords": []
  }
}
```

---

### POST /resumes/{id}/analyze
Re-trigger Groq AI analysis for a resume.

---

### PUT /resumes/{id}/primary
Set a resume as the primary/default.

---

### DELETE /resumes/{id}
Delete resume record and file.

---

## Jobs

### GET /jobs
List jobs with filters and pagination.

**Query params:**
| Param | Type | Description |
|---|---|---|
| `search` | string | Search in title, company, description |
| `location` | string | Filter by location |
| `employment_type` | string | Full-time, Part-time, Contract |
| `work_mode` | string | remote, hybrid, onsite |
| `source` | string | Adzuna, Remotive, JSearch |
| `sort` | string | -posted_at, -salary_max, title |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Results per page (default: 20, max: 100) |

**Response `200`:**
```json
{
  "items": [{ "id": "...", "title": "...", "company": "...", "location": "..." }],
  "total": 342,
  "page": 1,
  "per_page": 20,
  "total_pages": 18
}
```

---

### POST /jobs/discover
Trigger background job discovery from all configured sources.

**Response `200`:** `{ "message": "Job discovery started. New jobs will appear shortly." }`

---

### GET /jobs/matches
Get AI-matched jobs for the current user.

**Query params:** `min_score` (float), `category` (excellent/strong/good/moderate/low), `page`, `per_page`

---

### GET /jobs/saved
Get user's saved jobs.

---

### POST /jobs/{id}/save
Save a job for later.

---

### DELETE /jobs/{id}/save
Remove from saved.

---

### POST /jobs/{id}/match
Run AI matching for a specific job against user's resume + profile.

**Response `200`:**
```json
{
  "match_score": 84.5,
  "match_category": "strong",
  "skills_match": 90,
  "experience_match": 85,
  "matching_skills": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["Kubernetes"],
  "ai_recommendation": "Strong fit. Your Python and API experience aligns well...",
  "reasons_to_apply": ["5+ years experience matches requirement"],
  "concerns": ["No Kubernetes experience mentioned"]
}
```

---

## AI Endpoints

All AI endpoints call **Groq API on the backend**. The API key is never exposed to the frontend.

### POST /ai/analyze-resume
Re-analyze a resume with Groq.

**Request:** `{ "resume_id": "uuid" }`

---

### POST /ai/generate-cover-letter
Generate a tailored cover letter.

**Request:**
```json
{
  "job_id": "uuid",
  "resume_id": "uuid",
  "style": "professional | conversational | concise"
}
```
**Response:**
```json
{
  "subject_line": "Application for Senior Software Engineer",
  "cover_letter": "Dear Hiring Manager,\n\n...",
  "word_count": 187,
  "key_points_addressed": ["5 years Python experience", "API design"]
}
```

---

### POST /ai/generate-email
Generate professional outreach email.

**Request:**
```json
{
  "email_type": "hr_outreach | hiring_manager | cold_outreach | ...",
  "company_name": "Google",
  "company_website": "https://google.com",
  "contact_name": "Jane Smith",
  "contact_designation": "Engineering Manager",
  "job_title": "Senior Engineer",
  "tone": "professional | friendly | confident | conversational | concise",
  "additional_instructions": "..."
}
```
**Response:**
```json
{
  "subject_lines": ["Option 1", "Option 2", "Option 3"],
  "short_version": "50-80 word email...",
  "medium_version": "100-150 word email...",
  "detailed_version": "150-250 word email...",
  "reasoning": "Why this email works...",
  "suggestions": ["Improvement 1", "Improvement 2"]
}
```

**Email types:**
- `job_application` — Formal application for advertised role
- `hr_outreach` — Contact HR/recruiter proactively
- `hiring_manager` — Direct outreach to decision maker
- `cold_outreach` — No specific opening available
- `referral_request` — Ask employee for referral
- `recruiter_introduction` — Introduce yourself to recruiter
- `post_application_followup` — Follow up after applying
- `interview_thankyou` — Post-interview thank you
- `linkedin_connection` — LinkedIn connection request (300 chars)
- `linkedin_followup` — After connection accepted
- `networking` — General professional networking

---

### POST /ai/generate-linkedin-message
Generate LinkedIn message.

**Request:**
```json
{
  "message_type": "connection_request | recruiter_message | followup",
  "recipient_name": "Jane Smith",
  "recipient_title": "Engineering Manager",
  "company_name": "Google"
}
```

---

### POST /ai/research-company
AI-powered company research.

**Request:**
```json
{
  "company_name": "Stripe",
  "website": "https://stripe.com",
  "additional_context": "Looking for engineering roles"
}
```
**Response:**
```json
{
  "overview": "Stripe is a payments infrastructure company...",
  "industry": "Financial Technology",
  "products_services": ["Payment processing", "Billing API"],
  "tech_focus_areas": ["Payments", "Infrastructure", "Machine Learning"],
  "potential_departments_hiring": ["Engineering", "Product", "Data"],
  "confidence_score": 85,
  "disclaimer": "Information based on publicly available data..."
}
```

---

### POST /ai/interview-preparation
Generate interview prep questions.

**Request:** `{ "job_id": "uuid" }`

**Response includes:**
- `technical_questions[]` with difficulty + suggested answer
- `behavioral_questions[]` with STAR format answers
- `hr_questions[]`
- `company_specific_questions[]`
- `questions_to_ask_interviewer[]`
- `preparation_tips[]`

---

### POST /ai/customize-resume
Optimize resume content for a specific job.

**Request:** `{ "job_id": "uuid", "resume_id": "uuid" }`

**Response:**
```json
{
  "optimized_summary": "Rewritten summary...",
  "reordered_skills": ["Most relevant skills first"],
  "keywords_incorporated": ["ATS keywords added"],
  "changes_made": ["Reordered experience section", "Added Python keyword"],
  "missing_keywords": ["Skills to develop"]
}
```

---

### POST /ai/generate-application-answers
Generate answers to job application form questions.

**Request:**
```json
{
  "job_id": "uuid",
  "questions": [
    "Why do you want to work here?",
    "Describe a challenging project"
  ]
}
```

---

### POST /ai/analyze-interview-answer
Score and provide feedback on a practice answer.

**Request:**
```json
{
  "question": "Tell me about a time you led a team",
  "answer": "In my previous role...",
  "job_context": "Senior Engineer at Google"
}
```
**Response:**
```json
{
  "score": 7,
  "strengths": ["Specific example given", "Clear outcome"],
  "improvements": ["Add more quantifiable results"],
  "better_answer": "Improved version...",
  "tips": ["Use STAR format", "Quantify the impact"]
}
```

---

## Applications

### GET /applications
List applications with optional status filter.

**Query params:** `status`, `page`, `per_page`, `sort`

**Application statuses:** `saved`, `recommended`, `ready_to_apply`, `applied`, `under_review`, `recruiter_contacted`, `interview_scheduled`, `interview_completed`, `assessment_pending`, `offer_received`, `rejected`, `withdrawn`

---

### POST /applications
Create a new application record.

**Request:**
```json
{
  "job_id": "uuid",
  "status": "applied",
  "resume_id": "uuid",
  "cover_letter": "Dear...",
  "notes": "Applied through company website"
}
```

---

### PUT /applications/{id}
Update application status or details.

**Request:** Any subset:
```json
{
  "status": "interview_scheduled",
  "recruiter_name": "Jane Smith",
  "recruiter_email": "jane@company.com",
  "follow_up_date": "2026-12-01T00:00:00Z",
  "notes": "Interview on Dec 5th"
}
```

---

## Outreach

### GET /outreach
List outreach contacts/campaigns.

**Query params:** `status`, `search`, `page`, `per_page`

---

### POST /outreach
Create outreach contact record.

```json
{
  "company_name": "Google",
  "company_website": "https://google.com",
  "contact_name": "Jane Smith",
  "contact_designation": "HR Manager",
  "contact_email": "jane@google.com",
  "email_type": "hr_outreach",
  "email_subject": "Senior Engineer Inquiry",
  "generated_email": "Dear Jane..."
}
```

---

### PUT /outreach/{id}
Update outreach contact status.

**Statuses:** `new_prospect`, `research_completed`, `email_generated`, `ready_to_send`, `sent`, `follow_up_due`, `response_received`, `interested`, `not_interested`

---

## Email Integration (Gmail)

### GET /email/status
Check if Gmail is connected.

---

### GET /email/auth-url
Get Google OAuth authorization URL.

---

### POST /email/connect
Exchange OAuth code for Gmail access.

**Request:** `{ "code": "oauth_authorization_code" }`

---

### POST /email/draft
Create a Gmail draft.

**Request:**
```json
{
  "to_email": "recruiter@company.com",
  "subject": "Senior Engineer Application",
  "body": "Dear Jane,\n\n..."
}
```

---

### POST /email/send
**Send an email through Gmail.**

> ⚠️ This endpoint sends a real email. The frontend MUST display the full email to the user and require explicit confirmation before calling this endpoint.

**Request:**
```json
{
  "to_email": "recruiter@company.com",
  "subject": "Senior Engineer Application",
  "body": "Dear Jane,\n\n...",
  "outreach_contact_id": "uuid"
}
```

---

### GET /email/history
Get sent email history.

---

## Analytics

### GET /analytics/overview
Get job search performance summary.

**Response:**
```json
{
  "total_jobs_discovered": 1240,
  "high_match_jobs": 48,
  "saved_jobs": 23,
  "applications_submitted": 12,
  "emails_generated": 35,
  "outreach_sent": 18,
  "recruiter_responses": 4,
  "interviews_scheduled": 2,
  "offers_received": 0
}
```

---

### GET /analytics/applications
Application funnel and timeline data for charts.

---

### GET /analytics/outreach
Outreach response rates by email type.

---

### GET /analytics/job-matches
Match score distribution by category.

---

## Notifications

### GET /notifications
Get all notifications (latest 50).

**Response:**
```json
{
  "items": [{
    "id": "uuid",
    "type": "new_job_match",
    "title": "New High-Match Job",
    "message": "Senior Engineer at Google matches 92%",
    "is_read": false,
    "link": "/ai-matching",
    "created_at": "2026-11-24T10:00:00Z"
  }],
  "total": 12,
  "unread_count": 3
}
```

---

### PUT /notifications/{id}/read
Mark a notification as read.

---

### PUT /notifications/read-all
Mark all notifications as read.

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|---|---|
| `400` | Bad request — invalid input |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — insufficient permissions |
| `404` | Resource not found |
| `409` | Conflict — duplicate resource |
| `422` | Unprocessable — validation failed |
| `503` | Service unavailable — Groq API or external service down |
