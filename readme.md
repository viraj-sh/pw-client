<div align="center">

# **pw-client**

A user-side client for **[pw.live](https://www.pw.live/)**, providing a streamlined interface to access officially enrolled course materials such as **Notes, DPPs, Quizzes, Announcements, and Solutions**. Includes a fully working [API](https://github.com/viraj-sh/pw-client/wiki/API-Documentation), [MCP Server](https://github.com/viraj-sh/pw-client/wiki/MCP-Documentation) and [Frontend](https://github.com/viraj-sh/pw-client/wiki/Frontend-Documentation) (currently under development).

<a href="https://github.com/viraj-sh/pw-client/releases/latest">
  <img src="https://img.shields.io/github/v/release/viraj-sh/pw-client?label=Latest%20Release&color=green&style=flat-square&cacheSeconds=3600" alt="Release"/>
</a>
<a href="https://hub.docker.com/r/virajsh/pw-client">
  <img src="https://img.shields.io/docker/v/virajsh/pw-client?label=Docker&color=blue&sort=semver&style=flat-square" alt="Docker"/>
</a>
<a href="https://github.com/viraj-sh/pw-client/wiki">
  <img src="https://img.shields.io/badge/docs-wiki-orange?style=flat-square" alt="Wiki"/>
</a>

</div>

---

## Getting Started

The client can be run using a **[prebuilt release](https://github.com/viraj-sh/pw-client/releases/latest)** (recommended), **[built from source](#option-1-building-from-source-without-docker)**, or **[Docker](#option-2-running-with-docker)**. Quick deployment is also supported on **Render**.

<!-- Download Latest Releases -->
<div style="margin-bottom: 1em;">
  <!-- <strong style="font-size:1.1em;">Download Latest Releases:</strong> -->
  <div style="margin-top:0.5em;">
    <!-- <a href="https://github.com/viraj-sh/pw-client/releases/download/v1.3.0/pw-client.exe" target="_blank">
      <img src="https://img.shields.io/badge/Windows-x64-blue?style=flat-square" alt="Download Windows" />
    </a> -->
    <!-- <a href="https://github.com/viraj-sh/pw-client/releases/latest/download/pw-client-linux.tar.gz" target="_blank">
      <img src="https://img.shields.io/badge/Linux-x64-orange?style=flat-square" alt="Download Linux" />
    </a>
    <a href="https://github.com/viraj-sh/pw-client/releases/latest/download/pw-client-macos.zip" target="_blank">
      <img src="https://img.shields.io/badge/macOS-x64-lightgrey?style=flat-square" alt="Download macOS" />
    </a> -->
  </div>
</div>

<!-- Quick Deployment -->
<div style="margin-top:1.5em;">
  <strong style="font-size:1.1em;">Quick Deployment:</strong>
  <div style="margin-top:0.5em;">
    <a href="https://render.com/deploy?repo=https://github.com/viraj-sh/pw-client/tree/v3.0" target="_blank">
      <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render" width="180"/>
    </a>
  </div>
</div>

---

### Available Services

Once the client is running, the following endpoints are accessible (the host may vary, but the paths remain the same):

- **Frontend:** [http://localhost:8000](http://localhost:8000)
- **MCP Server:** [http://localhost:8000/mcp](http://localhost:8000/mcp)
- **API:** [http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)

  - **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)


---

## Option 1: Building from Source (Without Docker)

```bash
git clone https://github.com/viraj-sh/pw-client
cd pw-client

python -m venv venv

venv\Scripts\activate # Windows
source venv/bin/activate # macOS/Linux

pip install --upgrade pip
pip install -r requirements.txt

python app.py
```

---

## Option 2: Running with Docker

### 1. Use Prebuilt Image from Docker Hub (Recommended)

```bash
docker pull virajsh/pw-client:latest
docker run -p 8000:8000 virajsh/pw-client:latest
```

### 2. Build Locally

A `Dockerfile` is included in the repository.

```bash
git clone https://github.com/viraj-sh/pw-client
cd pw-client
docker build -t pw-client .
docker run -p 8000:8000 pw-client
```

### 3. Docker Compose

A [`docker-compose.yaml`](https://github.com/viraj-sh/pw-client/blob/v3.0/docker-compose.yaml) is included in the repository.

```bash
# using curl
curl -L -o docker-compose.yaml https://github.com/viraj-sh/pw-client/raw/v3.0/docker-compose.yaml 

# using wget
wget -O docker-compose.yaml https://github.com/viraj-sh/pw-client/raw/v3.0/docker-compose.yaml 

docker-compose up -d
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