# ⚡ CodeSense — AI-Powered Automated Code Review

> Automatically reviews your code every time you push to GitHub. Detects bugs, security vulnerabilities, and bad practices — instantly.

![CodeSense](https://img.shields.io/badge/CodeSense-Code%20Review-58a6ff?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql)
![GitHub Webhooks](https://img.shields.io/badge/GitHub-Webhooks-181717?style=for-the-badge&logo=github)

## 🚀 Live Demo

👉 **[Try CodeSense Live](https://codesense-ivory.vercel.app)**

---

## 🔍 What It Does

CodeSense automatically reviews your code every time you push to GitHub:

- 🚨 **Security Scanner** — Detects hardcoded secrets, eval() usage, SQL injection
- ⚠️ **Code Quality** — Finds long lines, bare except blocks, TODO comments
- 💡 **Suggestions** — Recommends logging over print(), proper exception handling
- 📊 **Score System** — Gives every push a quality score out of 100
- 🔀 **PR Comments** — Auto posts review summary directly on Pull Requests
- 📈 **Dashboard** — Beautiful React dashboard showing score trends over time
- 🔍 **Code Analyzer** — Paste any code snippet for instant review

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js, Recharts |
| Backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL (Supabase) |
| Integration | GitHub Webhooks |
| Deployment | Vercel (Frontend) + Render (Backend) |

---

## ⚙️ How It Works
Developer pushes code to GitHub
↓
GitHub sends webhook to CodeSense
↓
FastAPI backend fetches the diff
↓
Code analysis engine scans for issues
↓
Results saved to PostgreSQL database
↓
Auto comment posted on PR
↓
Dashboard updates in real time

---

## 🚀 Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/sharan-deep21/codesense.git
cd codesense
```

**2. Setup Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Create `.env` file in backend folder**
```bash
GITHUB_TOKEN=your_github_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SECRET_KEY=your_secret_key
```

**4. Run Backend**
```bash
python main.py
```

**5. Setup Frontend**
```bash
cd ../frontend
npm install
npm start
```

**6. Setup Webhook**
- Use ngrok to expose local backend: `ngrok http 8000`
- Add webhook to your GitHub repo pointing to: `https://your-ngrok-url/webhook/github`

---

## 📁 Project Structure
codesense/
├── backend/
│   ├── main.py           # FastAPI app + webhook handler
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables
├── frontend/
│   ├── src/
│   │   └── App.js       # React dashboard
│   └── package.json
└── README.md

---

## 🔑 What Gets Detected

### Security Issues 🚨
- Hardcoded passwords, tokens, API keys
- Dangerous `eval()` usage
- SQL injection vulnerabilities

### Code Quality ⚠️
- Lines over 120 characters
- Bare `except:` blocks
- TODO/FIXME comments

### Suggestions 💡
- `print()` statements in Python
- `console.log()` in JavaScript
- Missing function structure

---

## 👨‍💻 Author

**Sharan Deep**
- GitHub: [@sharan-deep21](https://github.com/sharan-deep21)
- LeetCode: [A-D21](https://leetcode.com/u/A-D21/)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

*Built with ❤️ — Automated code review for every developer*