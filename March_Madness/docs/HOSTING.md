# Hosting the March Madness Backend on Render

This guide covers local testing, optional Docker, and deployment to Render for the FastAPI backend in `api/server.py`.

## 1 Local Run (Mac)

Use **one** virtualenv at the **Git repo root** (parent of `March_Madness/`) and install from `requirements.txt` there. Then run the API from `March_Madness/`:

```bash
cd /path/to/HELLY's_DEVIL_MAGIC
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

cd March_Madness
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

Smoke tests:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/matchups/r64
curl -X POST http://127.0.0.1:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"sims": 2000, "temperature": 1.0, "pure_stochastic": false}'
```

## 2) Optional Docker Setup

Use the **repo root** as the Docker build context so the top-level `requirements.txt` is available. Example `Dockerfile` at `March_Madness/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY March_Madness /app/March_Madness

WORKDIR /app/March_Madness
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r ../requirements.txt

ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Build and run from the **repository root** (not from inside `March_Madness/`):

```bash
docker build -f March_Madness/Dockerfile -t mm-backend .
docker run --rm -p 8000:8000 mm-backend
```

If you must build with context `March_Madness/` only, copy the repo-root `requirements.txt` into that folder first so `pip install -r requirements.txt` can find it.

## 3) Deploy on Render (Recommended)

### 3.1 Push code to GitHub

Render deploys from Git, so push this repo (or a branch) to GitHub first.

### 3.2 Create Web Service

1. In Render dashboard: **New -> Web Service**
2. Connect GitHub repo
3. Set **Root Directory** to the **repo root** (parent of `March_Madness/`), so Render can read the top-level `requirements.txt`.

### 3.3 Choose runtime path

Use one of:

- **Native Python runtime**
  - Build Command: `pip install -U pip && pip install -r requirements.txt`
  - Start Command: `cd March_Madness && uvicorn api.server:app --host 0.0.0.0 --port $PORT`

- **Docker runtime**
  - Select Docker and let Render use your `Dockerfile`.

### 3.4 Environment and health checks

Set environment variables:

- `PYTHONUNBUFFERED=1`
- `MODEL_WARMUP=1` (optional marker if you later add conditional startup behavior)

Set health check path:

- `/health`

### 3.5 Deploy and verify

After deploy finishes, test:

```bash
curl https://YOUR-RENDER-URL.onrender.com/health
curl -X POST https://YOUR-RENDER-URL.onrender.com/simulate \
  -H "Content-Type: application/json" \
  -d '{"sims": 2000, "temperature": 1.0, "pure_stochastic": false}'
```

## 4) Connect from iOS

Use your Render URL as the app `baseURL`, for example:

- `https://YOUR-RENDER-URL.onrender.com`

## 5) Operational Notes

- Render free instances sleep when idle; first request after sleep can be slow due to model/context warmup.
- If cold starts become an issue, precompute/cache serialized artifacts and load them at boot.
- Updates are easiest by pushing commits to the configured branch (Render auto-deploy).
