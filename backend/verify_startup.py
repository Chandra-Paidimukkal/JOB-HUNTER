"""
Verifies the full backend startup stack:
  1. .env loaded correctly
  2. Groq API key valid + model working
  3. SQLite DB creates tables
  4. All models importable
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PASS = []
FAIL = []

def check(label, fn):
    try:
        result = fn()
        PASS.append(label)
        print(f"  OK  {label}" + (f" => {result}" if result else ""))
    except Exception as e:
        FAIL.append(label)
        print(f"  ERR {label}: {e}")

print("\n=== JobHunter AI — Startup Verification ===\n")

# 1. Config
check("Config loads", lambda: __import__("app.core.config").core.config.settings.APP_NAME)

# 2. Database engine
def test_db():
    from app.core.config import settings
    return f"Using: {settings.DATABASE_URL[:30]}..."
check("Database URL set", test_db)

# 3. All models
def test_models():
    import app.models
    return f"{len([m for m in dir(app.models) if not m.startswith('_')])} models"
check("All models import", test_models)

# 4. Create tables
def test_tables():
    from app.core.database import Base, engine
    import app.models  # register all models
    Base.metadata.create_all(bind=engine)
    return "tables created"
check("Database tables created", test_tables)

# 5. Security
def test_security():
    from app.core.security import hash_password, verify_password, create_access_token
    h = hash_password("testpass123")
    assert verify_password("testpass123", h)
    assert not verify_password("wrongpass", h)
    token = create_access_token("test-user-id")
    return "bcrypt + JWT OK"
check("Security (bcrypt + JWT)", test_security)

# 6. Groq API
def test_groq():
    from app.core.config import settings
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY not set in .env")
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": "Say: OK"}],
        max_tokens=5,
    )
    reply = response.choices[0].message.content.strip()
    return f"model={settings.GROQ_MODEL} reply='{reply}'"
check("Groq AI API (live call)", test_groq)

# 7. Resume parser imports
def test_parser():
    from app.services.resumes.parser import extract_resume_text
    return "PyMuPDF + python-docx ready"
check("Resume parser (PyMuPDF/docx)", test_parser)

# 8. Job connectors
def test_connectors():
    from app.integrations.job_sources.remotive import RemotiveConnector
    assert RemotiveConnector().is_configured()
    return "Remotive=free, Adzuna=needs key, JSearch=needs key"
check("Job connectors", test_connectors)

# 9. FastAPI app
def test_app():
    import app.main
    return "FastAPI app loaded"
check("FastAPI main app", test_app)

# --- Summary ---
print(f"\n{'='*45}")
print(f"  PASSED: {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAILED: {', '.join(FAIL)}")
else:
    print("  ALL CHECKS PASSED — Ready to launch!")
print(f"{'='*45}\n")
sys.exit(0 if not FAIL else 1)
