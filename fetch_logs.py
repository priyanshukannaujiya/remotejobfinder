import urllib.request
import json
import sys

# Get latest run
url = "https://api.github.com/repos/heypk4-dotcom/dataenginneringjob-finder/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        runs = data.get('workflow_runs', [])
        scraper_runs = [r for r in runs if r.get('name') == 'Daily Job Scraper']
        if not scraper_runs:
            print("No scraper runs found.")
            sys.exit(0)
        latest_run = scraper_runs[0]
        run_id = latest_run['id']
        print(f"Latest run ID: {run_id} at {latest_run['created_at']}")
        
        # Get jobs for this run
        jobs_url = f"https://api.github.com/repos/heypk4-dotcom/dataenginneringjob-finder/actions/runs/{run_id}/jobs"
        jobs_req = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla'})
        with urllib.request.urlopen(jobs_req) as j_resp:
            jobs_data = json.loads(j_resp.read().decode())
            jobs_list = jobs_data.get('jobs', [])
            if not jobs_list:
                print("No jobs found for run.")
                sys.exit(0)
                
            job_id = jobs_list[0]['id']
            # Get logs for this job
            log_url = f"https://api.github.com/repos/heypk4-dotcom/dataenginneringjob-finder/actions/jobs/{job_id}/logs"
            log_req = urllib.request.Request(log_url, headers={'User-Agent': 'Mozilla'})
            try:
                with urllib.request.urlopen(log_req) as l_resp:
                    logs = l_resp.read().decode('utf-8', errors='ignore')
                    print(logs[-2000:])
            except Exception as e:
                print("Could not fetch logs (might require authentication):", e)

except Exception as e:
    print(f"Error: {e}")
