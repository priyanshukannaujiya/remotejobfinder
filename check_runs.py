import urllib.request
import json
try:
    url = 'https://api.github.com/repos/heypk4-dotcom/dataenginneringjob-finder/actions/runs'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    run = data['workflow_runs'][0]
    print(f"Created At: {run['created_at']}")
    print(f"Updated At: {run['updated_at']}")
    print(f"Head Commit Message: {run['head_commit']['message']}")
    print(f"Status: {run['status']}")
    print(f"Conclusion: {run['conclusion']}")
except Exception as e:
    print(f"Error: {e}")
