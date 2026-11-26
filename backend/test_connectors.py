"""Test all job source connectors."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL = [], []

def check(label, fn):
    try:
        result = fn()
        PASS.append(label)
        print(f"  OK  {label}" + (f" => {result}" if result else ""))
        return result
    except Exception as e:
        FAIL.append(label)
        print(f"  ERR {label}: {e}")
        return None

print("\n=== Connector Import & Live Tests ===\n")

# Test imports
check("Remotive import", lambda: __import__("app.integrations.job_sources.remotive"))
check("WeWorkRemotely import", lambda: __import__("app.integrations.job_sources.weworkremotely_connector"))
check("Greenhouse import", lambda: __import__("app.integrations.job_sources.greenhouse_connector"))
check("Lever import", lambda: __import__("app.integrations.job_sources.lever_connector"))
check("Wellfound import", lambda: __import__("app.integrations.job_sources.wellfound_connector"))
check("Naukri import", lambda: __import__("app.integrations.job_sources.naukri_connector"))
check("JobSpy import", lambda: __import__("app.integrations.job_sources.jobspy_connector"))
check("Google Jobs import", lambda: __import__("app.integrations.job_sources.google_jobs_connector"))
check("Career Crawler import", lambda: __import__("app.integrations.job_sources.career_crawler"))
check("Discovery service import", lambda: __import__("app.services.jobs.discovery_service"))

print("\n--- Live connector tests ---\n")

# Remotive — always works
def test_remotive():
    from app.integrations.job_sources.remotive import RemotiveConnector
    c = RemotiveConnector()
    results = c.search(["python developer"], limit=5)
    return f"{len(results)} jobs: {results[0].title[:40] if results else 'none'}"
check("Remotive LIVE", test_remotive)

# WeWorkRemotely — always works
def test_wwr():
    from app.integrations.job_sources.weworkremotely_connector import WeWorkRemotelyConnector
    c = WeWorkRemotelyConnector()
    results = c.search(["python", "developer"], limit=5)
    return f"{len(results)} jobs: {results[0].title[:40] if results else 'none'}"
check("WeWorkRemotely LIVE", test_wwr)

# Greenhouse — always works
def test_greenhouse():
    from app.integrations.job_sources.greenhouse_connector import GreenhouseConnector
    c = GreenhouseConnector()
    results = c.search(["engineer"], limit=5)
    return f"{len(results)} jobs: {results[0].title[:40] if results else 'none'}"
check("Greenhouse LIVE", test_greenhouse)

# Lever — always works
def test_lever():
    from app.integrations.job_sources.lever_connector import LeverConnector
    c = LeverConnector()
    results = c.search(["engineer"], limit=5)
    return f"{len(results)} jobs: {results[0].title[:40] if results else 'none'}"
check("Lever LIVE", test_lever)

# Career crawler — test with Vercel (uses Greenhouse)
def test_career_crawler():
    from app.integrations.job_sources.career_crawler import CareerPageCrawler
    c = CareerPageCrawler()
    results = c.crawl_company("https://vercel.com", "Vercel", ["engineer"], limit=5)
    return f"{len(results)} jobs: {results[0].title[:40] if results else 'none'}"
check("Career Crawler LIVE (Vercel)", test_career_crawler)

# JobSpy — test LinkedIn/Indeed scrape
def test_jobspy():
    from app.integrations.job_sources.jobspy_connector import JobSpyConnector
    c = JobSpyConnector()
    results = c.search(["python developer"], location="Remote", limit=5)
    return f"{len(results)} jobs: {results[0].title[:40] if results else 'none'}"
check("JobSpy LIVE (LinkedIn+Indeed)", test_jobspy)

print(f"\n{'='*45}")
print(f"  PASSED: {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAILED: {', '.join(FAIL)}")
else:
    print("  ALL CONNECTOR TESTS PASSED!")
print(f"{'='*45}\n")
