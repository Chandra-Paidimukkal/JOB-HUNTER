"""Inspect OpenWebNinja job field structure."""
import sys, os, json, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

r = requests.get(
    "https://api.openwebninja.com/jsearch/search-v2",
    params={"query": "python developer remote", "page": 1},
    headers={"X-API-Key": "ak_2udvuymuf60o1b1zz3k5yfz12e2wb1wz8evwz1usa7etwb3"},
    timeout=20,
)
data = r.json()
inner = data.get("data", {})
jobs = inner.get("jobs", []) if isinstance(inner, dict) else []

print(f"\nTotal jobs in response: {len(jobs)}")
if jobs:
    j = jobs[0]
    print(f"\nAll field names in first job:")
    for k, v in j.items():
        val_preview = str(v)[:80] if v is not None else "null"
        print(f"  {k:40s} = {val_preview}")
