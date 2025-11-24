# **pw-client**
[![Latest Release](https://img.shields.io/github/v/release/viraj-sh/pw-client)]()
[![Downloads](https://img.shields.io/github/downloads/viraj-sh/pw-client/total)]()

A user-side client for **pw.live**, providing a streamlined interface to access officially enrolled course materials such as **Notes, DPPs, Quizzes, Announcements, and Solutions**.  
Includes a fully working **FastAPI backend** and **MCP server**, with a **frontend currently under development**.

---

# **Quick Deployment Options**

### Deploy to Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Prebuilt Release Binaries
Multi-platform binaries are available under **Releases**:
- Linux
- Windows
- macOS  

Download and run directly.

---

# **Unified Endpoints (Same For All Deployment Methods)**

Whether running locally, via Docker, Render, or release binaries:

- API → `/api`  
- API Docs (Swagger) → `/docs`  
- MCP Server → `/mcp`  
- Frontend (in development) → `/`

If running locally → `http://localhost:8000/...`  
If deployed → `https://your-domain/...`

Paths remain **exactly the same** across all environments.

---

# **Local Development**

### 1. Clone Repo
```bash
git clone https://github.com/viraj-sh/pw-client.git
cd pw-client
````

### 2. Virtual Environment + Install

```bash
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run API

```bash
python app.py
# or
uvicorn app:app --reload
```

---

# **Docker Deployment**

### Build & Run

```bash
docker build -t pw-client .
docker run -p 8000:8000 pw-client
```

### Using Prebuilt Image

```bash
docker run -p 8000:8000 virajsh/pw-client
```

### Using docker-compose

A docker-compose file is included in the repo:

**Download directly:**
[https://raw.githubusercontent.com/viraj-sh/pw-client/v3.0/docker-compose.yml](https://raw.githubusercontent.com/viraj-sh/pw-client/v3.0/docker-compose.yml)

```bash
docker compose up -d
```

---

# **Core Features (Minimal Overview)**

* Login via Phone + OTP
* Login via Bearer Token (preserves active pw.live session)
* Browse batches → subjects → chapters → documents
* Access notes, DPPs, quizzes, announcements
* View and download completed quiz solutions
* Fully featured MCP server (VS Code / Copilot / LLM ready)
* Legacy Streamlit version available in old branch

---

# **How to Obtain Your PW Session Token**

1. Log in to [https://www.pw.live/](https://www.pw.live/)
2. Open Developer Tools → Network
3. Refresh the page
4. Open the `verify-token` request
5. Copy the value after `Bearer` from the Authorization header
6. Paste it into the login field

---

## **Disclaimer**

This project is intended **only for legitimate pw.live users**.
Users may access only the study material belonging to their own enrolled courses.
No unauthorized access, scraping, or misuse of pw.live systems is supported.

---