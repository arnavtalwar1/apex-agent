# 🚀 APEX Agent Live Production Deployment Guide

This guide walks you through deploying **APEX Agent** live on production infrastructure using **Render / Railway** (for FastAPI Backend + Managed PostgreSQL) and **Vercel** (for Next.js 16 Frontend).

---

## 📋 Architecture in Production

```
+------------------------------------+          +------------------------------------+
|         Vercel (Frontend)          |          |      Render / Railway (Backend)     |
|   https://apex-agent.vercel.app    +--------->|   https://apex-backend.onrender.com |
|   Next.js 16 App Router + SSE      |  HTTPS   |   FastAPI + LangGraph Execution     |
+------------------------------------+          +-----------------+------------------+
                                                                  |
                                                                  v
                                                +------------------------------------+
                                                |     Managed PostgreSQL Database    |
                                                |     Users, Tasks, Reflections      |
                                                +------------------------------------+
```

---

## 🛠️ Step 1: Push Project to GitHub

Both Render and Vercel connect directly to your GitHub repository for continuous deployment.

1. **Initialize Git** in the project root:
   ```powershell
   git init
   git add .
   git commit -m "feat: prepare production deployment configurations"
   ```

2. **Create a new repository** on [GitHub](https://github.com/new) (e.g., `apex-agent`).

3. **Push your code**:
   ```powershell
   git branch -M main
   git remote add origin https://github.com/<your-username>/apex-agent.git
   git push -u origin main
   ```
   *(Note: `.env` and `apex.db` are strictly ignored by `.gitignore` so your local credentials remain secure).*

---

## 🐘 Step 2: Deploy Backend & PostgreSQL on Render

You have two simple options on [Render.com](https://render.com):

### Option A: 1-Click Render Blueprint (Recommended)
1. Log in to [Render](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Select your `apex-agent` repository.
4. Render will read the included [`render.yaml`](render.yaml) and automatically configure:
   - A free managed **PostgreSQL database** (`apex-db`).
   - A Web Service (`apex-backend`) with automatic database linking, Alembic migrations, and health checks.
5. In the environment variables prompt, enter your API key(s):
   - `OPENAI_API_KEY`: Your OpenAI API key (or `GROQ_API_KEY` / `OPENROUTER_API_KEY`).
   - `TAVILY_API_KEY`: (Optional) For web search capabilities.
6. Click **Apply**.
7. Once deployed, note down your live Backend URL (e.g., `https://apex-backend.onrender.com`).

---

### Option B: Manual Setup on Render
1. **Create PostgreSQL Database**:
   - Go to **New +** -> **PostgreSQL**.
   - Name: `apex-db`, Database: `apex`, User: `apex_user`, Plan: **Free**.
   - Click **Create Database**.
   - Once provisioned, copy the **Internal Database URL** (or External URL).

2. **Create Web Service**:
   - Go to **New +** -> **Web Service**.
   - Connect your GitHub repository.
   - **Environment**: `Python`
   - **Region**: Same as your database (e.g., `Oregon`).
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path**: `/health`

3. **Add Environment Variables**:
   | Variable | Value | Description |
   |---|---|---|
   | `DATABASE_URL` | *Paste connection string from PostgreSQL* | Auto-normalized to `postgresql+asyncpg://` |
   | `OPENAI_API_KEY` | `sk-...` | Primary LLM Provider Key |
   | `GROQ_API_KEY` | *(Optional)* | Groq API Key |
   | `OPENROUTER_API_KEY` | *(Optional)* | OpenRouter API Key |
   | `TAVILY_API_KEY` | *(Optional)* | Tavily Search Key |
   | `MODEL_NAME` | `gpt-4o-mini` | LLM Model |
   | `JWT_SECRET_KEY` | *(Generate a random 32+ character string)* | Session encryption key |
   | `ALLOWED_ORIGINS` | `*` | Or your Vercel URL |
   | `ALLOWED_HOSTS` | `*` | Allowed host headers |

4. Click **Deploy Web Service**. Verify that `https://<your-service>.onrender.com/health` returns:
   ```json
   {"status": "healthy"}
   ```

---

## ⚡ Step 3: Deploy Frontend on Vercel

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub `apex-agent` repository.
4. In the **Configure Project** settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click **Edit** and select `frontend`.
5. Under **Environment Variables**, add:
   | Key | Value | Example |
   |---|---|---|
   | `NEXT_PUBLIC_API_BASE` | `https://<YOUR-RENDER-BACKEND-URL>/api/v1` | `https://apex-backend.onrender.com/api/v1` |
6. Click **Deploy**.
7. Vercel will build and launch the Next.js app in under 60 seconds!

---

## 🌐 Step 4: Verification & Live Test

1. Visit your live Vercel URL (e.g., `https://apex-agent.vercel.app`).
2. Observe the top navigation bar:
   - The status badge should indicate `BACKEND ONLINE` (green).
3. Click **Register** (`/register`) and create your user account.
4. Log in and create your first agent task (e.g., *"Write a Python script that calculates Fibonacci numbers and plots them"*).
5. Watch the **LangGraph multi-agent live stream** run seamlessly in real-time over SSE!

---

## 🔄 Alternative: Deploying on Railway (All-in-One)

If you prefer **Railway.app**:
1. Go to [Railway](https://railway.com) -> **New Project**.
2. Click **Provision PostgreSQL**.
3. Click **Add Service** -> **GitHub Repo** -> select `apex-agent`.
4. Railway will automatically detect the [`Procfile`](Procfile) and `requirements.txt`.
5. In the Service Variables, link `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` and add `OPENAI_API_KEY` and `JWT_SECRET_KEY`.
6. Deploy and generate a domain.
