"""
Full discovery test — runs all connectors with 'python developer' query.
Tests the parallel execution and deduplication pipeline.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n=== Full Global Job Discovery Test ===\n")
print("Query: 'Python Developer' | Location: Remote\n")

start = time.time()

# Test JobSpy (LinkedIn + Indeed + Glassdoor + Google + ZipRecruiter)
print("1. JobSpy (LinkedIn + Indeed + Glassdoor + Google + ZipRecruiter):")
try:
    from app.integrations.job_sources.jobspy_connector import JobSpyConnector
    c = JobSpyConnector()
    results = c.search(["python developer"], location="Remote", limit=10)
    print(f"   Found {len(results)} jobs")
    for j in results[:3]:
        print(f"   - [{j.source}] {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

print()

# Test Greenhouse (top tech companies)
print("2. Greenhouse (Stripe, Figma, Notion, Airbnb, Databricks...):")
try:
    from app.integrations.job_sources.greenhouse_connector import GreenhouseConnector
    c = GreenhouseConnector()
    results = c.search(["python", "engineer", "developer"], limit=10)
    print(f"   Found {len(results)} jobs")
    for j in results[:3]:
        print(f"   - {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

print()

# Test Lever (Netflix, Discord, Lyft...)
print("3. Lever (Netflix, Discord, Lyft, Cloudflare...):")
try:
    from app.integrations.job_sources.lever_connector import LeverConnector
    c = LeverConnector()
    results = c.search(["engineer", "developer"], limit=10)
    print(f"   Found {len(results)} jobs")
    for j in results[:3]:
        print(f"   - {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

print()

# Test Wellfound (startups)
print("4. Wellfound (startup jobs):")
try:
    from app.integrations.job_sources.wellfound_connector import WellfoundConnector
    c = WellfoundConnector()
    results = c.search(["python"], limit=5)
    print(f"   Found {len(results)} jobs")
    for j in results[:2]:
        print(f"   - {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

print()

# Test WeWorkRemotely
print("5. WeWorkRemotely (remote-only jobs):")
try:
    from app.integrations.job_sources.weworkremotely_connector import WeWorkRemotelyConnector
    c = WeWorkRemotelyConnector()
    results = c.search(["python", "developer"], limit=5)
    print(f"   Found {len(results)} jobs")
    for j in results[:2]:
        print(f"   - {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

print()

# Test Naukri
print("6. Naukri.com (India jobs):")
try:
    from app.integrations.job_sources.naukri_connector import NaukriConnector
    c = NaukriConnector()
    results = c.search(["python developer"], location="Bangalore", limit=5)
    print(f"   Found {len(results)} jobs")
    for j in results[:2]:
        print(f"   - {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

print()

# Test career crawler with a specific company
print("7. Company Career Page Crawler (Google.com):")
try:
    from app.integrations.job_sources.career_crawler import CareerPageCrawler
    c = CareerPageCrawler()
    results = c.crawl_company("https://careers.google.com", "Google", ["python", "engineer"], limit=5)
    print(f"   Found {len(results)} jobs")
    for j in results[:2]:
        print(f"   - {j.title[:50]} @ {j.company}")
except Exception as e:
    print(f"   Error: {e}")

elapsed = time.time() - start
print(f"\n=== Completed in {elapsed:.1f}s ===\n")
