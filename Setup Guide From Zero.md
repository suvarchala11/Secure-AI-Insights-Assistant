# Setup Guide — From Zero to Running in Under 5 Minutes

## Prerequisites checklist
- [ ] Python 3.10 or higher → https://python.org/downloads
- [ ] Git → https://git-scm.com
- [ ] Ollama → https://ollama.com/download
- [ ] 4GB free disk space (for the AI model)
- [ ] 8GB RAM minimum recommended

---

## Option A — Docker (Easiest, Recommended)

### Step 1 — Install Docker Desktop
Download from https://docker.com/products/docker-desktop
Start Docker Desktop and wait for it to show "Engine running".

### Step 2 — Install and start Ollama
Download from https://ollama.com/download
Once installed, open a terminal and run:
ollama pull llama3.2:3b
This downloads the AI model (~2GB). Wait for it to complete.

### Step 3 — Clone and run
git clone https://github.com/suvarchala11/Secure-AI-Insights-Assistant.git

cd insights-assistant
docker compose up --build
First build takes 3-4 minutes (downloading Python packages).

### Step 4 — Open the app
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Option B — Manual Python Setup

### Step 1 — Install Ollama and pull the model
Download Ollama from https://ollama.com/download
ollama pull llama3.2:3b
ollama serve
Keep this terminal open.

### Step 2 — Clone the repository
git clone https://github.com/suvarchala11/Secure-AI-Insights-Assistant.git

cd insights-assistant

### Step 3 — Create Python virtual environment
macOS / Linux:
python3 -m venv venv
source venv/bin/activate
Windows:
python -m venv venv
venv\Scripts\activate

### Step 4 — Install Python dependencies
pip install -r requirements.txt
This takes 3-5 minutes on first run.

### Step 5 — Generate synthetic data
python generate_data.py
You should see 11 checkmarks confirming all files were created.

### Step 6 — Start the backend
uvicorn backend.main:app --reload --port 8000
Wait for: `═══ All data sources ready ═══`

### Step 7 — Open the frontend
Open `frontend/index.html` directly in Chrome or Firefox.
The green status dot confirms the backend is connected.

---

## Verify everything is working

Run these curl commands in a new terminal:
1. Health check (instant)
curl http://localhost:8000/health
2. Chart data (instant)
curl "http://localhost:8000/api/chart-data?chart_type=genre_views"
3. Chat (takes 15-25s on CPU — this is normal)
curl -X POST http://localhost:8000/api/chat 
-H "Content-Type: application/json" 
-d '{"question": "Which titles performed best in 2025?"}'

## Expected response times
| Endpoint | Expected time |
|---|---|
| /health | < 1 second |
| /api/chart-data | < 1 second |
| /api/chat | 15–30 seconds (CPU inference) |

## Troubleshooting

**"Backend offline" in frontend:**
→ Make sure `uvicorn` is running in another terminal tab.

**Chat returns error after 30s:**
→ Make sure `ollama serve` is running. Test with:
   `curl http://localhost:11434`

**"Module not found" errors:**
→ Make sure your virtualenv is activated:
   `source venv/bin/activate`

**Docker: "host.docker.internal not found" (Linux only):**
→ Already handled by `extra_hosts` in docker-compose.yml.
   If issues persist, set OLLAMA_BASE_URL=http://172.17.0.1:11434
