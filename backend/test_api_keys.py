"""
Live API key validation test for SerpAPI and OpenWebNinja.
"""
import sys, os, json, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SERPAPI_KEY    = "8d7dce7822dc5629c3323aa6166c3b4f43e159c6cc717582110f6248cd19d07f"
OWN_KEY        = "ak_2udvuymuf60o1b1zz3k5yfz12e2wb1wz8evwz1usa7etwb3"

PASS, FAIL = [], []

def check(label, fn):
    try:
        result = fn()
        PASS.append(label)
        print(f"  OK  {label} => {result}")
        return result
    except Exception as e:
        FAIL.append(label)
        print(f"  ERR {label}: {e}")
        return None

print("\n=== API Key Validation ===\n")

# ── 1. SerpAPI — Google Jobs ──────────────────────────────────
print("1. SerpAPI (Google Jobs):")
def test_serpapi():
    r = requests.get(
        "https://serpapi.com/search",
        params={
            "engine": "google_jobs",
            "q": "python developer remote",
            "api_key": SERPAPI_KEY,
            "num": 3,
        },
        timeout=20,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    data = r.json()
    jobs = data.get("jobs_results", [])
    if jobs:
        j = jobs[0]
        print(f"      Sample: '{j.get('title')}' @ {j.get('company_name')}")
        print(f"      Via: {j.get('via')} | Location: {j.get('location')}")
    return f"{len(jobs)} jobs found"
check("SerpAPI Google Jobs", test_serpapi)

print()

# ── 2. OpenWebNinja JSearch ───────────────────────────────────
print("2. OpenWebNinja JSearch:")
def test_own():
    r = requests.get(
        "https://api.openwebninja.com/jsearch/search-v2",
        params={"query": "python developer remote", "page": 1},
        headers={"X-API-Key": OWN_KEY},
        timeout=20,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:300]}"
    data = r.json()

    # Print full structure to understand field names
    print(f"      Response keys: {list(data.keys())}")

    # Try multiple possible locations for the job list
    jobs = (
        data.get("data") or
        data.get("jobs") or
        data.get("results") or
        data.get("job_listings") or
        []
    )

    if jobs and isinstance(jobs, list) and len(jobs) > 0:
        j = jobs[0]
        print(f"      Total jobs: {len(jobs)}")
        print(f"      First job keys: {list(j.keys())[:15]}")
        title = j.get("job_title") or j.get("title") or j.get("position") or "?"
        company = j.get("employer_name") or j.get("company") or j.get("company_name") or "?"
        print(f"      Sample: '{title}' @ {company}")
        print(f"      Location: {j.get('job_city')}, {j.get('job_country')}")
        print(f"      Apply URL: {(j.get('job_apply_link') or j.get('apply_link') or j.get('url', ''))[:80]}")
    elif isinstance(data, list) and len(data) > 0:
        # Response itself is an array
        j = data[0]
        print(f"      Array response: {len(data)} items")
        print(f"      First item keys: {list(j.keys())[:15]}")
        jobs = data

    return f"{len(jobs)} jobs"
raw_data = check("OpenWebNinja JSearch", test_own)

# Also test the original example from the user
print()
print("3. OpenWebNinja — exact user example:")
def test_own_exact():
    headers = {"X-API-Key": "ak_2udvuymuf60o1b1zz3k5yfz12e2wb1wz8evwz1usa7etwb3"}
    response = requests.request(
        'GET',
        'https://api.openwebninja.com/jsearch/search-v2',
        params={"query": "developer jobs in chicago"},
        headers=headers,
        timeout=20,
    )
    print(f"      HTTP Status: {response.status_code}")
    data = response.json()
    # Show first 500 chars of raw response
    raw = json.dumps(data)[:600]
    print(f"      Raw response (first 600 chars):\n      {raw}")
    return f"HTTP {response.status_code}"
check("OpenWebNinja exact example", test_own_exact)

print(f"\n{'='*50}")
print(f"  PASSED: {len(PASS)}/{len(PASS)+len(FAIL)}")
if FAIL:
    print(f"  FAILED: {', '.join(FAIL)}")
print(f"{'='*50}\n")
