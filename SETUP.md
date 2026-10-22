# VibeBreaker Setup & Run Guide

This guide walks you through setting up and running the VibeBreaker full-stack application (FastAPI backend + Next.js frontend).

---

## Prerequisites

- **Python**: 3.10+ (tested on Python 3.11 / 3.12 / 3.14)
- **Node.js**: 18.0+ and `npm`
- *(Optional)* **DigitalOcean Inference API Key**: If omitted, VibeBreaker automatically runs in **Demo / Mock Mode** so you can develop and test immediately without an API key.

---

## 1. Backend Setup (FastAPI)

### Step 1: Open a terminal and navigate to `api`
```bash
cd api
```
*(If working inside the `vibebreaker` subfolder, run `cd vibebreaker/api`)*

### Step 2: (Recommended) Create and activate a Python virtual environment

**Windows (PowerShell or Command Prompt):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables (optional)
Copy the example environment file:
```bash
# Windows PowerShell
cp .env.example .env

# macOS / Linux
cp .env.example .env
```

If you have a DigitalOcean Inference API Key, open `.env` and set:
```ini
DIGITALOCEAN_INFERENCE_API_KEY=your_key_here
DIGITALOCEAN_INFERENCE_BASE_URL=https://inference.do-ai.run
VIBEBREAKER_MODEL_NAME=qwen2.5-coder-32b-instruct
DATABASE_URL=sqlite:///./vibebreaker.db
APP_HOST=0.0.0.0
APP_PORT=8000
```
> **Note:** If `DIGITALOCEAN_INFERENCE_API_KEY` is not set or empty, the backend automatically runs in offline mock/demo mode.

### Step 5: Start the backend server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify backend is healthy by visiting:
[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) or [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) — it should return:
```json
{"status": "ok", "service": "VibeBreaker API"}
```

---

## 2. Frontend Setup (Next.js)

### Step 1: Open a second terminal and navigate to `web`
```bash
cd web
```
*(If working inside the `vibebreaker` subfolder, run `cd vibebreaker/web`)*

### Step 2: Install dependencies
```bash
npm install
```

### Step 3: Configure frontend environment
Create or check `.env.local`:
```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 4: Start the frontend development server
```bash
npm run dev
```

The application is now live at:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## Troubleshooting & Tips

### Port 8000 Already in Use (`[Errno 10048]`)
If you see:
```text
ERROR: [Errno 10048] error while attempting to bind on address ...
```
This means an existing uvicorn process or service is already holding port 8000.

**To fix on Windows (PowerShell):**
```powershell
# 1. Find the PID using port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess -Unique

# 2. Terminate the process (replace <PID> with the number from above)
taskkill /F /PID <PID>
```
Or run on a different port:
```bash
python -m uvicorn app.main:app --port 8001 --reload
```
*(If you change to port 8001, update `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001` in `web/.env.local`)*

### Port 3000 Already in Use
Run Next.js on port 3001:
```bash
npm run dev -- -p 3001
```

### Running Backend Tests
To test the complete session flow (create, get, attempt, hint, viva questions):
```bash
python final_test.py
```
or
```bash
python test_flow.py
```
