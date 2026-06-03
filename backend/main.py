from fastapi import FastAPI, Request
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

@app.get("/")
def root():
    return {"status": "AI Code Review Assistant is running"}

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
            
            return {
                "status": "PR received",
                "pr_number": pr_number,
                "repo": repo_name,
                "title": pr_title
            }
    
    return {"status": "event ignored"}