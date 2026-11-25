"""Run this to verify all backend imports work correctly."""
import sys
import os

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

errors = []


def test(label, mod):
    try:
        __import__(mod)
        print(f"OK  {label}")
    except Exception as e:
        print(f"ERR {label}: {e}")
        errors.append((label, str(e)))


test("config", "app.core.config")
test("database", "app.core.database")
test("security", "app.core.security")
test("user models", "app.models.user")
test("job models", "app.models.job")
test("resume models", "app.models.resume")
test("outreach models", "app.models.outreach")
test("notification models", "app.models.notification")
test("all models", "app.models")
test("ai groq client", "app.services.ai.groq_client")
test("resume parser", "app.services.resumes.parser")
test("resume service", "app.services.resumes.resume_service")
test("job discovery", "app.services.jobs.discovery_service")
test("auth endpoints", "app.api.v1.endpoints.auth")
test("profile endpoints", "app.api.v1.endpoints.profile")
test("jobs endpoints", "app.api.v1.endpoints.jobs")
test("ai endpoints", "app.api.v1.endpoints.ai")
test("applications", "app.api.v1.endpoints.applications")
test("outreach", "app.api.v1.endpoints.outreach")
test("analytics", "app.api.v1.endpoints.analytics")
test("notifications", "app.api.v1.endpoints.notifications")
test("email integration", "app.api.v1.endpoints.email_integration")
test("v1 router", "app.api.v1.router")
test("main app", "app.main")

print("\n" + "=" * 50)
if errors:
    print(f"FAILURES ({len(errors)}):")
    for label, err in errors:
        print(f"  - {label}: {err[:100]}")
else:
    print("ALL IMPORTS SUCCESSFUL ✓")
