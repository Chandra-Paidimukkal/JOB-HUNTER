"""
Full live search test with both API keys active.
Tests SerpAPI (Google Jobs) + OpenWebNinja + all free connectors.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

KEYWORDS = ["python developer", "software engineer"]
LOCATION = "Remote"

print(f"\n=== Live Multi-Source Job Search ===")
print(f"Keywords: {KEYWORDS}")
print(f"Location: {LOCATION}\n")

results_summary = {}

# 1. OpenWebNinja (LinkedIn + Indeed + Glassdoor)
print("1. OpenWebNinja (LinkedIn + Indeed + Glassdoor + ZipRecruiter):")
t = time.time()
try:
    from app.integrations.job_sources.openwebninja_connector import OpenWebNinjaConnector
    c = OpenWebNinjaConnector()
    if c.is_configured():
        jobs = c.search(KEYWORDS, location=LOCATION, limit=20)
        results_summary["OpenWebNinja"] = len(jobs)
        print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
        for j in jobs[:5]:
            sal = f" ${j.salary_min/1000:.0f}k-${j.salary_max/1000:.0f}k" if j.salary_min else ""
            print(f"   - [{j.source.split('/')[-1]}] {j.title[:45]:<45} @ {j.company:<25}{sal}")
    else:
        print("   ✗ Not configured")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# 2. Google Jobs via SerpAPI
print("2. Google Jobs (SerpAPI — covers 1000s of company sites):")
t = time.time()
try:
    from app.integrations.job_sources.google_jobs_connector import GoogleJobsConnector
    c = GoogleJobsConnector()
    if c.is_configured():
        jobs = c.search(KEYWORDS, location=LOCATION, limit=10)
        results_summary["Google Jobs"] = len(jobs)
        print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
        for j in jobs[:5]:
            sal = f" ${j.salary_min/1000:.0f}k-${j.salary_max/1000:.0f}k" if j.salary_min else ""
            src = j.source.replace("Google/","")
            print(f"   - [{src:<12}] {j.title[:45]:<45} @ {j.company:<25}{sal}")
    else:
        print("   ✗ Not configured")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# 3. Greenhouse (top tech companies)
print("3. Greenhouse (Airbnb, Stripe, Figma, Notion, OpenAI, Databricks...):")
t = time.time()
try:
    from app.integrations.job_sources.greenhouse_connector import GreenhouseConnector
    c = GreenhouseConnector()
    jobs = c.search(["engineer", "developer", "python"], limit=10)
    results_summary["Greenhouse"] = len(jobs)
    print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
    for j in jobs[:5]:
        print(f"   - {j.title[:45]:<45} @ {j.company}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# 4. Lever (Netflix, Discord, Cloudflare...)
print("4. Lever (Netflix, Discord, Cloudflare, Lyft, Rippling...):")
t = time.time()
try:
    from app.integrations.job_sources.lever_connector import LeverConnector
    c = LeverConnector()
    jobs = c.search(["engineer", "developer"], limit=10)
    results_summary["Lever"] = len(jobs)
    print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
    for j in jobs[:5]:
        print(f"   - {j.title[:45]:<45} @ {j.company}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# 5. WeWorkRemotely
print("5. WeWorkRemotely (remote-first jobs):")
t = time.time()
try:
    from app.integrations.job_sources.weworkremotely_connector import WeWorkRemotelyConnector
    c = WeWorkRemotelyConnector()
    jobs = c.search(["python", "developer"], limit=5)
    results_summary["WeWorkRemotely"] = len(jobs)
    print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
    for j in jobs[:3]:
        print(f"   - {j.title[:45]:<45} @ {j.company}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# 6. Remotive
print("6. Remotive (global remote jobs):")
t = time.time()
try:
    from app.integrations.job_sources.remotive import RemotiveConnector
    c = RemotiveConnector()
    jobs = c.search(KEYWORDS[:1], limit=5)
    results_summary["Remotive"] = len(jobs)
    print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
    for j in jobs[:3]:
        print(f"   - {j.title[:45]:<45} @ {j.company}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# 7. Naukri
print("7. Naukri.com (India jobs):")
t = time.time()
try:
    from app.integrations.job_sources.naukri_connector import NaukriConnector
    c = NaukriConnector()
    jobs = c.search(["python developer"], location="Bangalore", limit=5)
    results_summary["Naukri"] = len(jobs)
    print(f"   ✓ {len(jobs)} jobs found in {time.time()-t:.1f}s")
    for j in jobs[:3]:
        print(f"   - {j.title[:45]:<45} @ {j.company}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Summary
total = sum(results_summary.values())
print(f"\n{'='*60}")
print(f"  TOTAL JOBS FOUND: {total}")
for src, count in results_summary.items():
    bar = "█" * min(count, 40)
    print(f"  {src:<20} {bar} {count}")
print(f"{'='*60}\n")
