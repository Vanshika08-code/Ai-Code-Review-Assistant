# this is a test
from fastapi import FastAPI, Request
import hmac
import hashlib
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

@app.get("/")
def root():
    return {"status": "AI Code Review Assistant is running"}

async def fetch_pr_diff(repo_name: str, pr_number: int):
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/files"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        files = response.json()
    
    diff_text = ""
    for file in files:
        filename = file["filename"]
        patch = file.get("patch", "No changes")
        diff_text += f"\n\n--- {filename} ---\n{patch}"
    
    return diff_text

@app.post("/webhook")
async def github_webhook(request: Request):
    body = await request.body()
    event_type = request.headers.get("X-GitHub-Event")
    
    if event_type == "pull_request":
        payload = await request.json()
        action = payload.get("action")
        
        if action in ["opened", "synchronize"]:
            pr_number = payload["pull_request"]["number"]
            repo_name = payload["repository"]["full_name"]
            pr_title = payload["pull_request"]["title"]
            
            print(f"New PR received: #{pr_number} - {pr_title} in {repo_name}")
            
            # Fetch the actual code changes
            diff = await fetch_pr_diff(repo_name, pr_number)
            print(f"Code diff fetched:\n{diff}")
            
            return {
                "status": "PR received",
                "pr_number": pr_number,
                "repo": repo_name,
                "title": pr_title,
                "diff_preview": diff[:500]  # first 500 chars as preview
            }
    
    return {"status": "event ignored"}