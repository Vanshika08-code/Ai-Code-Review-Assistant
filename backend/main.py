from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "AI Code Review Assistant is running"}