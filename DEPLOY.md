# Deployment Guide — Render (Backend) + Vercel (Frontend)

This guide explains how to deploy **InNovus / AppForge AI** with:

- **Backend** on [Render](https://render.com) (Python / FastAPI)
- **Frontend** on [Vercel](https://vercel.com) (React / Vite)

---

## Prerequisites

- GitHub repository with the project pushed
- Accounts on [Render](https://render.com) and [Vercel](https://vercel.com)
- API keys for **Groq** and **HuggingFace**

---

## 1. Deploy the Backend on Render

### 1.1 Create a new Web Service

1. Go to [Render Dashboard](https://dashboard.render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `appforge-backend` (or any name) |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Root Directory** | *(leave blank — backend files are at repo root)* |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend_mode:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free (or Starter for better performance) |

### 1.2 Set Environment Variables

In the Render dashboard, add these **Environment Variables**:

| Key | Value | Notes |
|-----|-------|-------|
| `GROQ_API_KEY` | `gsk_...` | Your Groq API key |
| `HUGGINGFACE_API_KEY` | `hf_...` | Your HuggingFace API key |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` | Your Vercel frontend URL (add after Vercel deploy) |
| `PORT` | *(set automatically by Render)* | Do not set manually |

### 1.3 Deploy

Click **Create Web Service**. Render will install dependencies and start the server.

Once deployed, note the URL (e.g. `https://appforge-backend.onrender.com`).

### 1.4 Verify

Open `https://appforge-backend.onrender.com/api/health` in your browser. You should see:

```json
{"status": "ok"}
```

---

## 2. Deploy the Frontend on Vercel

### 2.1 Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New → Project**
2. Import your GitHub repo
3. Configure:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend_v2/frontend_app` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

### 2.2 Set Environment Variables

In Vercel project settings → **Environment Variables**, add:

| Key | Value | Notes |
|-----|-------|-------|
| `VITE_API_URL` | `https://appforge-backend.onrender.com` | Your Render backend URL (**no trailing slash**) |

> The frontend uses `VITE_API_URL` to construct API calls in production. In local development, the Vite proxy handles routing to `localhost:8000` so this variable is not needed.

### 2.3 Deploy

Click **Deploy**. Vercel will build the Vite app and serve it.

Your app will be live at `https://your-app.vercel.app`.

### 2.4 Update CORS on Render

Go back to your Render service's environment variables and update:

```
ALLOWED_ORIGINS=https://your-app.vercel.app
```

If you have multiple allowed origins (e.g. a custom domain), separate them with commas:

```
ALLOWED_ORIGINS=https://your-app.vercel.app,https://yourdomain.com
```

Render will auto-redeploy after saving.

---

## 3. Local Development

### Backend

```bash
# From project root
pip install -r requirements.txt
python backend_mode.py
# Runs on http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend_v2/frontend_app
npm install
npm run dev
# Runs on http://localhost:5173 — proxies /api to :8000
```

No environment variables needed locally. The Vite dev server proxy handles API routing.

---

## 4. Environment Variable Reference

### Backend (Render)

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM chat |
| `HUGGINGFACE_API_KEY` | Yes | HuggingFace key for code generation |
| `ALLOWED_ORIGINS` | Recommended | Comma-separated allowed CORS origins (defaults to `*`) |
| `HOST` | No | Bind address (default `127.0.0.1`, Render overrides via start command) |
| `PORT` | No | Port (default `8000`, Render sets this automatically) |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes (prod) | Full URL of the Render backend, e.g. `https://appforge-backend.onrender.com` |

---

## 5. Architecture Overview

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  Vercel (Frontend)       │         │  Render (Backend)        │
│                          │         │                          │
│  React + Vite            │  HTTPS  │  FastAPI + Uvicorn       │
│  Static SPA              │────────▶│  /api/chat/simple        │
│                          │         │  /api/chat/tailored      │
│  VITE_API_URL ───────────┼────────▶│  /api/generate           │
│                          │         │  /api/generate/tailored  │
│                          │         │  /api/pipeline/*         │
│                          │         │  /api/health             │
│                          │         │                          │
│                          │         │  SQLite DB               │
│                          │         │  Groq + HuggingFace APIs │
└──────────────────────────┘         └──────────────────────────┘
```

---

## 6. Troubleshooting

| Problem | Solution |
|---------|----------|
| CORS errors in browser console | Set `ALLOWED_ORIGINS` on Render to your Vercel URL |
| Frontend shows "Backend unavailable" | Check `VITE_API_URL` is set correctly on Vercel (no trailing slash) |
| Render deploy fails | Check `requirements.txt` has all dependencies; check build logs |
| Vercel build fails | Ensure **Root Directory** is set to `frontend_v2/frontend_app` |
| API returns 500 | Check Render logs; verify `GROQ_API_KEY` and `HUGGINGFACE_API_KEY` are set |
| Render free tier sleeps | Free instances spin down after inactivity; first request may take ~30s |
| SQLite issues on Render | SQLite works on Render but data is ephemeral on free tier (lost on redeploy) |
