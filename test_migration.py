"""Test the repo migration API endpoint."""
import uvicorn
from threading import Thread
import time
import requests

def run_server():
    from devassist.api.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

# Start server
t = Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

# Test endpoint
r = requests.post(
    "http://127.0.0.1:8000/api/migrate/repo", 
    json={
        "repo_url": "https://github.com/HustleDanie/legacy-python2-app", 
        "migration_type": "py2to3"
    }
)
print("Status:", r.status_code)
job = r.json()
job_id = job["job_id"]
print("Job ID:", job_id)

# Poll for status
for i in range(30):
    time.sleep(2)
    try:
        status_r = requests.get(f"http://127.0.0.1:8000/api/jobs/{job_id}")
        if status_r.status_code == 404:
            print(f"Check {i+1}: Job not found (404)")
            continue
        status = status_r.json()
        print(f"Check {i+1}: status={status.get('status', 'unknown')}, agent={status.get('current_agent', 'N/A')}")
        
        if status.get("error"):
            print("ERROR:", status["error"])
        
        if status.get("status") in ["completed", "failed"]:
            print("\n=== Final Status ===")
            print("Messages:")
            for msg in status.get("messages", []):
                print(f"  - {msg}")
            print(f"Files: {status.get('file_count', 0)}")
            print(f"Issues Found: {status.get('issues_found', 0)}")
            print(f"Issues Fixed: {status.get('issues_fixed', 0)}")
            print(f"Tests Passed: {status.get('tests_passed')}")
            print(f"PR URL: {status.get('pr_url')}")
            break
    except Exception as e:
        print(f"Check {i+1}: Error - {e}")

print("\nDone!")
