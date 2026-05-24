from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
import json
import hmac
import hashlib

load_dotenv()

app = FastAPI(title="CodeSense API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def supabase_insert(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        **SUPABASE_HEADERS,
        "Prefer": "return=representation"
    }
    res = requests.post(url, headers=headers, json=data)
    print(f"Supabase insert status: {res.status_code}")
    print(f"Supabase insert response: {res.text}")
    return res.json()

def supabase_select(table, filters=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}"
    res = requests.get(url, headers={**SUPABASE_HEADERS, "Prefer": "return=representation"})
    return res.json()

@app.get("/")
def root():
    return {"message": "CodeSense API is running!", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/webhook/github")
async def github_webhook(request: Request):
    body = await request.body()
    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(body)

    if event == "push":
        return await handle_push(payload)
    elif event == "pull_request":
        return await handle_pull_request(payload)

    return {"message": f"Event {event} received but not processed"}

async def handle_push(payload):
    repo = payload.get("repository", {})
    commits = payload.get("commits", [])
    pusher = payload.get("pusher", {})

    repo_name = repo.get("full_name", "")
    repo_url = repo.get("html_url", "")
    branch = payload.get("ref", "").replace("refs/heads/", "")

    all_files = []
    for commit in commits:
        all_files.extend(commit.get("added", []))
        all_files.extend(commit.get("modified", []))

    code_files = [f for f in all_files if any(
        f.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
    )]

    review_results = []
    for file_path in code_files[:5]:
        content = get_file_content(repo_name, file_path, payload.get("after", ""))
        if content:
            review = analyze_code(content, file_path)
            review_results.append({"file": file_path, "review": review})

    overall_score = calculate_overall_score(review_results)

    review_data = {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "branch": branch,
        "pusher": pusher.get("name", "unknown"),
        "commit_sha": payload.get("after", ""),
        "files_reviewed": len(review_results),
        "overall_score": overall_score,
        "results": json.dumps(review_results),
        "event_type": "push"
    }

    supabase_insert("reviews", review_data)

    return {"message": "Push reviewed", "score": overall_score, "files": len(review_results)}

async def handle_pull_request(payload):
    action = payload.get("action", "")
    if action not in ["opened", "synchronize"]:
        return {"message": "PR action not tracked"}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    repo_name = repo.get("full_name", "")
    pr_number = pr.get("number")
    pr_title = pr.get("title", "")
    pr_url = pr.get("html_url", "")
    author = pr.get("user", {}).get("login", "")

    files = get_pr_files(repo_name, pr_number)
    code_files = [f for f in files if any(
        f["filename"].endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
    )]

    review_results = []
    for file_info in code_files[:5]:
        patch = file_info.get("patch", "")
        if patch:
            review = analyze_code(patch, file_info["filename"])
            review_results.append({"file": file_info["filename"], "review": review})

    overall_score = calculate_overall_score(review_results)

    comment = generate_pr_comment(review_results, overall_score, pr_title)
    post_pr_comment(repo_name, pr_number, comment)

    review_data = {
        "repo_name": repo_name,
        "repo_url": pr_url,
        "branch": pr.get("head", {}).get("ref", ""),
        "pusher": author,
        "commit_sha": pr.get("head", {}).get("sha", ""),
        "files_reviewed": len(review_results),
        "overall_score": overall_score,
        "results": json.dumps(review_results),
        "event_type": "pull_request",
        "pr_number": pr_number,
        "pr_title": pr_title
    }

    supabase_insert("reviews", review_data)

    return {"message": "PR reviewed", "score": overall_score}

def get_file_content(repo, path, sha):
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={sha}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        import base64
        content = res.json().get("content", "")
        try:
            return base64.b64decode(content).decode("utf-8")
        except:
            return ""
    return ""

def get_pr_files(repo, pr_number):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def analyze_code(code, filename):
    issues = []
    suggestions = []
    security = []
    score = 100

    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        line_lower = line.lower().strip()

        # Security checks
        if any(secret in line_lower for secret in ["password=", "secret=", "api_key=", "token="]):
            if "=" in line and not line_lower.startswith("#"):
                security.append({
                    "line": i,
                    "severity": "critical",
                    "message": "Possible hardcoded secret detected",
                    "code": line.strip()[:80]
                })
                score -= 20

        if "eval(" in line_lower:
            security.append({
                "line": i,
                "severity": "critical",
                "message": "Dangerous eval() usage detected",
                "code": line.strip()[:80]
            })
            score -= 15

        if "execute(" in line_lower and "%" in line:
            security.append({
                "line": i,
                "severity": "critical",
                "message": "Possible SQL injection vulnerability",
                "code": line.strip()[:80]
            })
            score -= 20

        # Code quality checks
        if len(line) > 120:
            issues.append({
                "line": i,
                "severity": "warning",
                "message": f"Line too long ({len(line)} chars). Keep under 120.",
                "code": line.strip()[:80]
            })
            score -= 2

        if "TODO" in line or "FIXME" in line or "HACK" in line:
            issues.append({
                "line": i,
                "severity": "info",
                "message": "Found TODO/FIXME comment — consider resolving",
                "code": line.strip()[:80]
            })

        if "print(" in line and filename.endswith(".py"):
            suggestions.append({
                "line": i,
                "severity": "suggestion",
                "message": "Use logging instead of print() in production code",
                "code": line.strip()[:80]
            })
            score -= 1

        if "console.log(" in line and filename.endswith((".js", ".ts")):
            suggestions.append({
                "line": i,
                "severity": "suggestion",
                "message": "Remove console.log() before production",
                "code": line.strip()[:80]
            })
            score -= 1

        if "except:" in line or "catch(e)" in line.replace(" ", ""):
            issues.append({
                "line": i,
                "severity": "warning",
                "message": "Avoid bare except/catch — specify exception types",
                "code": line.strip()[:80]
            })
            score -= 5

    # Complexity check
    if filename.endswith(".py"):
        func_count = sum(1 for l in lines if l.strip().startswith("def "))
        if func_count == 0 and len(lines) > 50:
            suggestions.append({
                "line": 0,
                "severity": "suggestion",
                "message": "Consider breaking this file into functions for better readability",
                "code": ""
            })

    return {
        "filename": filename,
        "score": max(score, 0),
        "security": security,
        "issues": issues,
        "suggestions": suggestions,
        "lines_analyzed": len(lines),
        "summary": {
            "critical": len(security),
            "warnings": len(issues),
            "suggestions": len(suggestions)
        }
    }

def calculate_overall_score(review_results):
    if not review_results:
        return 100
    scores = [r["review"]["score"] for r in review_results]
    return int(sum(scores) / len(scores))

def generate_pr_comment(review_results, overall_score, pr_title):
    emoji = "✅" if overall_score >= 80 else "⚠️" if overall_score >= 60 else "❌"

    comment = f"""## 🔍 CodeSense Review

{emoji} **Overall Score: {overall_score}/100**

> Automated code review for: _{pr_title}_

---

"""
    for result in review_results:
        review = result["review"]
        file_emoji = "🟢" if review["score"] >= 80 else "🟡" if review["score"] >= 60 else "🔴"
        comment += f"### {file_emoji} `{review['filename']}` — Score: {review['score']}/100\n\n"

        if review["security"]:
            comment += "**🚨 Security Issues:**\n"
            for issue in review["security"][:3]:
                comment += f"- Line {issue['line']}: {issue['message']}\n"
            comment += "\n"

        if review["issues"]:
            comment += "**⚠️ Warnings:**\n"
            for issue in review["issues"][:3]:
                comment += f"- Line {issue['line']}: {issue['message']}\n"
            comment += "\n"

        if review["suggestions"]:
            comment += "**💡 Suggestions:**\n"
            for s in review["suggestions"][:3]:
                comment += f"- Line {s['line']}: {s['message']}\n"
            comment += "\n"

    comment += "---\n*Powered by [CodeSense](https://github.com/sharan-deep21) — Automated Code Review*"
    return comment

def post_pr_comment(repo, pr_number, comment):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    requests.post(url, headers=HEADERS, json={"body": comment})

@app.get("/reviews")
def get_reviews(repo: str = None):
    if repo:
        filters = f"repo_name=eq.{repo}&order=created_at.desc&limit=20"
    else:
        filters = "order=created_at.desc&limit=20"
    return supabase_select("reviews", filters)

@app.get("/reviews/{review_id}")
def get_review(review_id: int):
    filters = f"id=eq.{review_id}"
    results = supabase_select("reviews", filters)
    if not results:
        raise HTTPException(status_code=404, detail="Review not found")
    return results[0]

@app.get("/stats")
def get_stats(repo: str = None):
    reviews = get_reviews(repo)
    if not reviews or isinstance(reviews, dict):
        return {"total_reviews": 0, "avg_score": 0, "total_files": 0}

    total = len(reviews)
    avg_score = int(sum(r.get("overall_score", 0) for r in reviews) / total) if total > 0 else 0
    total_files = sum(r.get("files_reviewed", 0) for r in reviews)

    return {
        "total_reviews": total,
        "avg_score": avg_score,
        "total_files": total_files,
        "recent_reviews": reviews[:5]
    }

@app.post("/analyze-snippet")
async def analyze_snippet(request: Request):
    data = await request.json()
    code = data.get("code", "")
    filename = data.get("filename", "snippet.py")
    result = analyze_code(code, filename)
    return result
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)