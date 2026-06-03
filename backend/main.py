from fastapi import FastAPI, Request
import os
import httpx
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

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

async def review_with_gemini(diff: str) -> str:
    prompt = f"""You are an expert code reviewer.
Review the following code changes from a Pull Request.
Give clear, helpful feedback on:
- Bugs or errors
- Code quality
- Security issues
- Suggestions to improve

Code changes:
{diff}

Give your review in a clear, structured format."""

    response = model.generate_content(prompt)
    return response.text

async def post_review_comment(repo_name: str, pr_number: int, review: str):
    url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    body = {"body": f"## 🤖 AI Code Review\n\n{review}"}

    async with httpx.AsyncClient() as client:
        await client.post(url, json=body, headers=headers)

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

            diff = await fetch_pr_diff(repo_name, pr_number)
            print(f"Diff fetched successfully")

            review = await review_with_gemini(diff)
            print(f"Gemini review done:\n{review}")

            await post_review_comment(repo_name, pr_number, review)
            print(f"Review posted on PR!")

            return {"status": "review posted", "pr_number": pr_number}

    return {"status": "event ignored"}