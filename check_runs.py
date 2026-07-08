import urllib.request
import json
import sys

url = "https://api.github.com/repos/heypk4-dotcom/dataenginneringjob-finder/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        runs = data.get('workflow_runs', [])
        if not runs:
            print("No runs found.")
        for r in runs[:10]:
            print(f"{r.get('name')} - {r.get('status')} - {r.get('conclusion')} - {r.get('created_at')}")
except Exception as e:
    print(f"Error fetching data: {e}")
