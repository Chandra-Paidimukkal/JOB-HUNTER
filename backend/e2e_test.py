"""
Live end-to-end test of all major workflows.
Backend must be running on http://127.0.0.1:8000
"""
import requests
import json
import time

BASE = "http://127.0.0.1:8000/api/v1"
PASS = []
FAIL = []

def check(label, fn):
    try:
        result = fn()
        PASS.append(label)
        print(f"  OK  {label}" + (f" => {result}" if result else ""))
        return result
    except AssertionError as e:
        FAIL.append(label)
        print(f"  FAIL {label}: {e}")
        return None
    except Exception as e:
        FAIL.append(label)
        print(f"  ERR  {label}: {e}")
        return None

print("\n=== JobHunter AI — Live E2E Test ===\n")

# ── 1. Health ────────────────────────────────────────────────────
def test_health():
    r = requests.get("http://127.0.0.1:8000/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    return r.json()["environment"]
check("GET /health", test_health)

# ── 2. Register ──────────────────────────────────────────────────
TOKEN = None
USER_ID = None

def test_register():
    global TOKEN, USER_ID
    import random, string
    suffix = ''.join(random.choices(string.digits, k=6))
    r = requests.post(f"{BASE}/auth/register", json={
        "email": f"e2e_{suffix}@jobhunter.ai",
        "password": "securepass123",
        "full_name": "E2E Test User",
    }, timeout=10)
    assert r.status_code == 201, f"Got {r.status_code}: {r.text}"
    data = r.json()
    TOKEN = data["access_token"]
    USER_ID = data["user"]["id"]
    return f"user_id={USER_ID[:8]}..."
check("POST /auth/register", test_register)

H = lambda: {"Authorization": f"Bearer {TOKEN}"}

# ── 3. Get current user ──────────────────────────────────────────
def test_me():
    r = requests.get(f"{BASE}/auth/me", headers=H(), timeout=5)
    assert r.status_code == 200
    return r.json()["email"]
check("GET /auth/me", test_me)

# ── 4. Complete onboarding ───────────────────────────────────────
def test_onboarding():
    r = requests.post(f"{BASE}/profile/onboarding", headers=H(), json={
        "personal": {
            "full_name": "Alex Johnson",
            "phone": "+1 555 123 4567",
            "current_location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/alexjohnson",
        },
        "professional": {
            "current_title": "Senior Software Engineer",
            "current_company": "TechCorp",
            "total_experience_years": 6,
            "technical_skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
            "soft_skills": ["Leadership", "Problem Solving"],
            "professional_summary": "Experienced engineer with 6 years building scalable web apps.",
        },
        "preferences": {
            "preferred_titles": ["Senior Engineer", "Staff Engineer", "Tech Lead"],
            "preferred_countries": ["USA", "UK"],
            "remote_ok": True,
            "hybrid_ok": True,
            "full_time": True,
            "expected_salary": 160000,
            "currency": "USD",
        },
        "objective": {
            "career_objective": "Lead engineering teams building AI-powered products",
            "short_term_goals": "Become a Staff Engineer within 2 years",
            "long_term_goals": "VP Engineering at a Series B startup",
        },
    }, timeout=15)
    assert r.status_code == 200, f"{r.status_code}: {r.text}"
    return "onboarding complete"
check("POST /profile/onboarding", test_onboarding)

# ── 5. Get profile ───────────────────────────────────────────────
def test_profile():
    r = requests.get(f"{BASE}/profile", headers=H(), timeout=5)
    assert r.status_code == 200
    p = r.json()["profile"]
    assert p["current_title"] == "Senior Software Engineer"
    return f"skills={p['technical_skills'][:3]}"
check("GET /profile", test_profile)

# ── 6. Update preferences ────────────────────────────────────────
def test_prefs():
    r = requests.put(f"{BASE}/profile/preferences", headers=H(), json={
        "preferred_cities": ["San Francisco", "New York", "Austin"],
        "min_salary": 130000,
    }, timeout=5)
    assert r.status_code == 200
    return "preferences updated"
check("PUT /profile/preferences", test_prefs)

# ── 7. Job discovery (Remotive — free) ───────────────────────────
def test_discover():
    r = requests.post(f"{BASE}/jobs/discover", headers=H(), timeout=10)
    assert r.status_code == 200
    return r.json()["message"]
check("POST /jobs/discover", test_discover)

# Wait for background discovery
time.sleep(3)

# ── 8. List jobs ─────────────────────────────────────────────────
def test_list_jobs():
    r = requests.get(f"{BASE}/jobs?per_page=5", headers=H(), timeout=10)
    assert r.status_code == 200
    data = r.json()
    return f"total={data['total']}, page={data['page']}"
check("GET /jobs (list)", test_list_jobs)

# ── 9. Create application ────────────────────────────────────────
APP_ID = None
JOB_ID = None

def test_create_app():
    global APP_ID, JOB_ID
    # Get first job
    r = requests.get(f"{BASE}/jobs?per_page=1", headers=H(), timeout=10)
    jobs = r.json().get("items", [])
    if not jobs:
        raise AssertionError("No jobs found — discovery may still be running")
    JOB_ID = jobs[0]["id"]
    # Create application
    r2 = requests.post(f"{BASE}/applications", headers=H(), json={
        "job_id": JOB_ID,
        "status": "saved",
        "notes": "Looks like a great fit!",
    }, timeout=10)
    assert r2.status_code == 201, f"{r2.status_code}: {r2.text}"
    APP_ID = r2.json()["id"]
    return f"app_id={APP_ID[:8]}... job={jobs[0]['title'][:30]}"
check("POST /applications", test_create_app)

# ── 10. Update application status ───────────────────────────────
def test_update_app():
    if not APP_ID:
        raise AssertionError("No app_id from previous step")
    r = requests.put(f"{BASE}/applications/{APP_ID}", headers=H(), json={
        "status": "applied",
        "recruiter_name": "Jane Smith",
        "recruiter_email": "jane@company.com",
    }, timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "applied"
    return "status=applied"
check("PUT /applications/{id}", test_update_app)

# ── 11. Analytics overview ───────────────────────────────────────
def test_analytics():
    r = requests.get(f"{BASE}/analytics/overview", headers=H(), timeout=5)
    assert r.status_code == 200
    d = r.json()
    return f"apps={d['applications_submitted']}, jobs={d['total_jobs_discovered']}"
check("GET /analytics/overview", test_analytics)

# ── 12. Groq — Company research ──────────────────────────────────
def test_company_research():
    r = requests.post(f"{BASE}/ai/research-company", headers=H(), json={
        "company_name": "Stripe",
        "website": "https://stripe.com",
        "additional_context": "Looking for engineering roles",
    }, timeout=30)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    d = r.json()
    assert "industry" in d or "overview" in d
    return f"industry='{d.get('industry', 'N/A')}' confidence={d.get('confidence_score', 'N/A')}"
check("POST /ai/research-company (Groq live)", test_company_research)

# ── 13. Groq — Generate email ────────────────────────────────────
def test_generate_email():
    r = requests.post(f"{BASE}/ai/generate-email", headers=H(), json={
        "email_type": "hr_outreach",
        "company_name": "Stripe",
        "company_website": "https://stripe.com",
        "company_industry": "Financial Technology",
        "contact_name": "Sarah Chen",
        "contact_designation": "Engineering Manager",
        "job_title": "Senior Software Engineer",
        "tone": "professional",
        "additional_instructions": "Focus on Python and API experience",
    }, timeout=45)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
    d = r.json()
    assert "subject_lines" in d
    assert len(d["subject_lines"]) >= 1
    assert "medium_version" in d
    return f"subject='{d['subject_lines'][0][:50]}...'"
check("POST /ai/generate-email (Groq live)", test_generate_email)

# ── 14. Create outreach record ───────────────────────────────────
def test_outreach():
    r = requests.post(f"{BASE}/outreach", headers=H(), json={
        "company_name": "Stripe",
        "company_website": "https://stripe.com",
        "contact_name": "Sarah Chen",
        "contact_designation": "Engineering Manager",
        "email_type": "hr_outreach",
        "status": "email_generated",
    }, timeout=10)
    assert r.status_code == 201
    return f"id={r.json()['id'][:8]}..."
check("POST /outreach", test_outreach)

# ── 15. Notifications ────────────────────────────────────────────
def test_notifications():
    r = requests.get(f"{BASE}/notifications", headers=H(), timeout=5)
    assert r.status_code == 200
    return f"count={r.json()['total']}"
check("GET /notifications", test_notifications)

# ── 16. Email status ─────────────────────────────────────────────
def test_email_status():
    r = requests.get(f"{BASE}/email/status", headers=H(), timeout=5)
    assert r.status_code == 200
    return f"connected={r.json()['connected']}"
check("GET /email/status", test_email_status)

# ── Summary ──────────────────────────────────────────────────────
print(f"\n{'='*45}")
print(f"  PASSED : {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAILED : {', '.join(FAIL)}")
    print("\n  Check error messages above.")
else:
    print("  ALL E2E TESTS PASSED")
    print("\n  Your JobHunter AI is fully operational!")
    print("  Open: http://localhost:3000")
print(f"{'='*45}\n")
